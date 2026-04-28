import pandas as pd
import numpy as np
import scipy.sparse as sp
import pickle
import os
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD          # LSA semantic embeddings
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
import shap

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocessing import preprocess_text
from utils.scoring import get_rule_features


def load_datasets(base_dir, data_root, custom_path):
    frames = []

    loaders = [
        ("SMSSpamCollection (TSV)",   dict(filepath_or_buffer=os.path.join(data_root, 'SMSSpamCollection'),     sep='\t', names=['label','text'])),
        ("SMSSpamCollection.csv",     dict(filepath_or_buffer=os.path.join(data_root, 'SMSSpamCollection.csv'), sep=',',  header=None, names=['raw'])),
        ("SpamCollectionSMS.txt",     dict(filepath_or_buffer=os.path.join(data_root, 'SpamCollectionSMS.txt'), sep='\t', names=['label','text'])),
    ]

    for name, kwargs in loaders:
        try:
            df = pd.read_csv(**kwargs, encoding='utf-8', on_bad_lines='skip')
            if 'raw' in df.columns:
                parsed = df['raw'].str.split('\t', n=1, expand=True)
                parsed.columns = ['label', 'text']
                df = parsed
            df['label'] = df['label'].map({'ham': 'safe', 'spam': 'scam'})
            frames.append(df)
            print(f"  [+] {name}: {len(df)} records")
        except Exception as e:
            print(f"  [-] {name}: {e}")

    # Custom CSV
    try:
        df = pd.read_csv(custom_path)
        df['label'] = df['label'].map(lambda x: 'scam' if x in ['phishing','fraud','scam','spam'] else 'safe')
        frames.append(df)
        print(f"  [+] Custom dataset: {len(df)} records")
    except Exception as e:
        print(f"  [-] Custom dataset: {e}")

    # Synthetic JSON
    try:
        df = pd.read_json(os.path.join(base_dir, 'data', 'scam_dataset.json'))
        df['label'] = df['label'].map({0: 'safe', 1: 'scam', 2: 'scam'})
        frames.append(df)
        print(f"  [+] Synthetic JSON: {len(df)} records")
    except Exception as e:
        print(f"  [-] Synthetic JSON: {e}")

    combined = pd.concat(frames, ignore_index=True).dropna()
    combined = combined.drop_duplicates(subset=['text'], keep='first')
    return combined


def build_features(texts_clean, texts_raw, word_vec, char_vec, lsa, fit=False):
    """
    Build combined feature matrix:
      [word_tfidf | char_tfidf | LSA semantic (200d) | rule features]
    LSA = TruncatedSVD on a large TF-IDF → gives document semantic embeddings
    without needing PyTorch / sentence-transformers.
    All combined as dense numpy for LightGBM.
    """
    if fit:
        X_word = word_vec.fit_transform(texts_clean)
        X_char = char_vec.fit_transform(texts_clean)
        X_lsa  = lsa.fit_transform(X_word)          # semantic: (n, 200)
    else:
        X_word = word_vec.transform(texts_clean)
        X_char = char_vec.transform(texts_clean)
        X_lsa  = lsa.transform(X_word)

    X_rules = np.array([get_rule_features(t) for t in texts_raw])

    # Combine: all to dense, then hstack
    return np.hstack([
        X_word.toarray(),
        X_char.toarray(),
        X_lsa,          # 200-dim semantic space
        X_rules         # 7 binary rule signals
    ])


def train_model():
    base_dir  = os.path.dirname(os.path.dirname(__file__))
    data_root = os.path.join(base_dir, '..', '..')
    custom_path = os.path.join(base_dir, 'data', 'custom_scam.csv')
    models_dir  = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)

    # ── STEP 1: LOAD ──────────────────────────────────────────────────
    print("=" * 60)
    print("STEP 1: Loading datasets...")
    print("=" * 60)
    df = load_datasets(base_dir, data_root, custom_path)
    print(f"\n  Total unique records: {len(df)}")
    print(f"  Safe: {(df['label']=='safe').sum()} | Scam: {(df['label']=='scam').sum()}")

    # ── STEP 2: PREPROCESS ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Preprocessing...")
    print("=" * 60)
    df['text_clean'] = df['text'].apply(preprocess_text)
    X_raw   = df['text'].tolist()
    X_clean = df['text_clean'].tolist()
    y = df['label'].map({'safe': 0, 'scam': 1}).values

    X_raw_tr, X_raw_te, X_cl_tr, X_cl_te, y_tr, y_te = train_test_split(
        X_raw, X_clean, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── STEP 3: FEATURE ENGINEERING ───────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Building Features — Word TF-IDF + Char TF-IDF + LSA Semantics + Rules")
    print("=" * 60)

    # Word-level bigrams
    word_vec = TfidfVectorizer(max_features=5000, ngram_range=(1,2), min_df=3, max_df=0.85, stop_words='english')
    # Character-level n-grams (catches typos, abbreviations)
    char_vec = TfidfVectorizer(max_features=2000, analyzer='char_wb', ngram_range=(3,5), min_df=2, max_df=0.90)
    # LSA: 200-dim semantic space via TruncatedSVD on word TF-IDF
    # This is the semantic layer — captures topic/meaning without PyTorch
    lsa = TruncatedSVD(n_components=200, random_state=42)

    print("  Building TRAIN features (LSA semantic decomposition)...")
    X_tr = build_features(X_cl_tr, X_raw_tr, word_vec, char_vec, lsa, fit=True)
    print(f"  Train feature matrix: {X_tr.shape}")

    print("  Building TEST features...")
    X_te = build_features(X_cl_te, X_raw_te, word_vec, char_vec, lsa, fit=False)
    print(f"  Test  feature matrix: {X_te.shape}")

    print(f"\n  Feature breakdown:")
    print(f"    Word TF-IDF:     {len(word_vec.vocabulary_)}")
    print(f"    Char TF-IDF:     {len(char_vec.vocabulary_)}")
    print(f"    LSA Semantics:   200  (TruncatedSVD — topics/meaning)")
    print(f"    Rule signals:    7")
    print(f"    TOTAL:           {X_tr.shape[1]}")

    # ── STEP 4: TRAIN LightGBM ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Training LightGBM Classifier...")
    print("=" * 60)

    lgbm = LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )
    lgbm.fit(X_tr, y_tr, eval_set=[(X_te, y_te)])
    print("  LightGBM training complete.")

    # ── STEP 5: CALIBRATE ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Calibrating probabilities (sigmoid method)...")
    print("=" * 60)
    calibrated = CalibratedClassifierCV(lgbm, method='sigmoid', cv=5)
    calibrated.fit(X_tr, y_tr)
    print("  Calibration complete.")

    # ── STEP 6: EVALUATE ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: Evaluation (soft thresholds: 0.40 / 0.72)")
    print("=" * 60)
    probs = calibrated.predict_proba(X_te)[:, 1]
    preds = np.where(probs >= 0.40, 1, 0)

    print(f"  Accuracy: {accuracy_score(y_te, preds):.4f}\n")
    print(classification_report(y_te, preds, target_names=['Safe','Scam']))

    cm = confusion_matrix(y_te, preds)
    tn, fp, fn, tp = cm.ravel()
    print(f"  TN:{tn}  FP:{fp}  FN:{fn}  TP:{tp}")

    # ── STEP 7: SHAP ANALYSIS ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: SHAP Feature Importance (TreeExplainer on raw LightGBM)...")
    print("=" * 60)
    explainer = shap.TreeExplainer(lgbm)
    # Use a sample of 200 for speed
    sample_idx = np.random.choice(len(X_te), min(200, len(X_te)), replace=False)
    shap_values = explainer.shap_values(X_te[sample_idx])

    # Build feature names
    all_feature_names = (
        list(word_vec.get_feature_names_out()) +
        list(char_vec.get_feature_names_out()) +
        [f"bert_{i}" for i in range(384)] +
        ["rule:urgency", "rule:fear", "rule:authority", "rule:greed",
         "rule:action", "rule:social", "rule:emotional"]
    )

    # Mean absolute SHAP values for scam class
    shap_arr = np.abs(shap_values[1]) if isinstance(shap_values, list) else np.abs(shap_values)
    mean_shap = shap_arr.mean(axis=0)
    top_idx = np.argsort(mean_shap)[-20:][::-1]
    print("\n  Top 20 features by SHAP importance:")
    for i in top_idx:
        print(f"    {all_feature_names[i]:35s}  SHAP: {mean_shap[i]:.4f}")

    # Save SHAP importances for dashboard
    shap_importance = {all_feature_names[i]: float(mean_shap[i]) for i in top_idx}
    with open(os.path.join(models_dir, 'shap_importance.pkl'), 'wb') as f:
        pickle.dump(shap_importance, f)

    # ── STEP 8: SMOKE TEST ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 8: Smoke Test")
    print("=" * 60)
    test_msgs = [
        ("Call me bro",                                    "SAFE"),
        ("Are you free tonight?",                          "SAFE"),
        ("Reply fast bro we need to leave",                "SAFE"),
        ("Hey I changed my number dont tell anyone",       "SUSPICIOUS"),
        ("Don't tell anyone, just follow what I say",      "SUSPICIOUS"),
        ("Send me the OTP you just received",              "SCAM"),
        ("Your account is blocked act now",                "SCAM"),
        ("You won Rs 5000 click now to claim prize",       "SCAM"),
        ("Click this link to confirm your delivery",       "SCAM"),
        ("I accidentally sent money please return it",     "SCAM"),
    ]
    for msg, expected in test_msgs:
        clean = preprocess_text(msg)
        feat  = build_features([clean], [msg], word_vec, char_vec, lsa, fit=False)
        prob  = calibrated.predict_proba(feat)[0][1]
        if prob < 0.40:   tag, ok = "[SAFE]      ", "SAFE"
        elif prob < 0.72: tag, ok = "[SUSPICIOUS]", "SUSPICIOUS"
        else:             tag, ok = "[SCAM]      ", "SCAM"
        match = "OK" if ok == expected else f"EXPECTED {expected}"
        print(f"  {tag} [{prob:.3f}] {match:20s} <- {msg}")

    # ── STEP 9: SAVE ARTIFACTS ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: Saving artifacts...")
    print("=" * 60)

    with open(os.path.join(models_dir, 'word_vectorizer.pkl'), 'wb') as f: pickle.dump(word_vec, f)
    with open(os.path.join(models_dir, 'char_vectorizer.pkl'), 'wb') as f: pickle.dump(char_vec, f)
    with open(os.path.join(models_dir, 'lsa.pkl'),             'wb') as f: pickle.dump(lsa, f)
    with open(os.path.join(models_dir, 'model.pkl'),           'wb') as f: pickle.dump(calibrated, f)
    with open(os.path.join(models_dir, 'lgbm_raw.pkl'),        'wb') as f: pickle.dump(lgbm, f)
    with open(os.path.join(models_dir, 'feature_names.pkl'),   'wb') as f: pickle.dump(all_feature_names, f)

    print(f"  Saved: word_vectorizer, char_vectorizer, lsa, model (calibrated), lgbm_raw, feature_names, shap_importance")
    print(f"\n{'=' * 60}")
    print(f"Training complete on {len(df)} records.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train_model()
