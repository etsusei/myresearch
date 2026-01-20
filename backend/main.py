"""
Music Exploration Experiment - Backend API
基于 gui_cluster_v2.py 的逻辑实现
"""
import os
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from scipy.stats import pearsonr
import json
import uuid
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════
# Data files are in backend/data/ directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GT_FILE = os.path.join(DATA_DIR, "music_data_2.npz")
PRED_FILE = os.path.join(DATA_DIR, "music_data_pred.npz")
FEATURE_FILE = os.path.join(DATA_DIR, "audio_features.csv")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# Axis Mapping (from gui_cluster_v2.py)
# ═══════════════════════════════════════════════════════════
AXIS_MAPPING = {
    'energy':           ('Intensity',        '强度',  '強度',  'Soft', '柔和', 'ソフト', 'Powerful', '强劲', 'パワフル'),
    'rms':              ('Loudness',         '响度',  '音量',  'Quiet', '安静', '静か', 'Loud', '响亮', '大きい'),
    'energy_std':       ('Dynamic Range',    '动态范围', 'ダイナミクス', 'Flat', '平坦', '平坦', 'Dynamic', '起伏', 'ダイナミック'),
    'bpm':              ('Tempo',            '速度',  'テンポ', 'Slow', '慢', '遅い', 'Fast', '快', '速い'),
    'danceability':     ('Groove',           '律动感', 'グルーヴ', 'Still', '静止', '静か', 'Danceable', '适合跳舞', 'ダンサブル'),
    'beats_loudness':   ('Beat Strength',    '节拍强度', 'ビート強度', 'Weak', '弱', '弱い', 'Strong', '强', '強い'),
    'onset_rate':       ('Note Density',     '音符密度', '音符密度', 'Sparse', '稀疏', '疎', 'Dense', '密集', '密'),
    'spectral_centroid':('Brightness',       '明亮度', '明るさ', 'Dark', '暗沉', '暗い', 'Bright', '明亮', '明るい'),
    'hfc':              ('High-Frequency',   '高频', '高周波', 'Muffled', '沉闷', 'こもった', 'Crisp', '清脆', 'クリア'),
    'spectral_rolloff': ('Sharpness',        '锐度', 'シャープさ', 'Warm', '温暖', '温かい', 'Sharp', '尖锐', '鋭い'),
    'spectral_flux':    ('Timbre Variation', '音色变化', '音色変化', 'Stable', '稳定', '安定', 'Varying', '多变', '変化'),
    'spectral_entropy': ('Instrumentation',  '配器复杂度', '楽器構成', 'Simple', '简单', 'シンプル', 'Complex', '复杂', '複雑'),
    'spectral_flatness_db': ('Sound Texture','声音质感', '音質感', 'Pure', '纯净', '純粋', 'Noisy', '嘈杂', 'ノイジー'),
    'dissonance':       ('Tension',          '紧张感', '緊張感', 'Consonant', '和谐', '協和', 'Dissonant', '不和谐', '不協和'),
    'key_strength':     ('Tonal Clarity',    '调性清晰度', '調性の明確さ', 'Ambiguous', '模糊', '曖昧', 'Clear', '清晰', '明確'),
}

CORRELATION_THRESHOLD = 0.25
DIFF_THRESHOLD = 0.10

app = FastAPI(title="Music Exploration Experiment API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════
class DataStore:
    def __init__(self):
        self.gt_data = None
        self.pred_data = None
        self.features_df = None
        self.loaded = False
    
    def load(self):
        if self.loaded:
            return
        
        print("Loading data...")
        
        # Load GT data
        if os.path.exists(GT_FILE):
            data = np.load(GT_FILE)
            self.gt_data = {
                'embeddings': data['embeddings'],
                'genres': data['genres'],
                'emotions': data['emotions'],
                'ids': data['ids']
            }
            print(f"Loaded GT: {len(self.gt_data['ids'])} songs")
        else:
            print(f"Warning: GT file not found: {GT_FILE}")
        
        # Load Pred data
        if os.path.exists(PRED_FILE):
            data = np.load(PRED_FILE)
            self.pred_data = {
                'embeddings': data['embeddings'],
                'genres': data['genres'],
                'emotions': data['emotions'],
                'ids': data['ids']
            }
            print(f"Loaded Pred: {len(self.pred_data['ids'])} songs")
        else:
            print(f"Warning: Pred file not found: {PRED_FILE}")
        
        # Load features
        if os.path.exists(FEATURE_FILE):
            self.features_df = pd.read_csv(FEATURE_FILE)
            self.features_df['id'] = self.features_df['id'].astype(str)
            print(f"Loaded features: {len(self.features_df)} songs")
        else:
            print(f"Warning: Feature file not found: {FEATURE_FILE}")
        
        self.loaded = True

data_store = DataStore()

@app.on_event("startup")
async def startup():
    data_store.load()

# ═══════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════
class AnalysisRequest(BaseModel):
    genre: str
    emotion: str
    version: str  # 'A' or 'B'
    version_mapping: Dict[str, str]  # {'A': 'GT', 'B': 'Model'} or vice versa
    auto_k: bool = True
    manual_k: int = 3

class SubmitRequest(BaseModel):
    session_data: Dict[str, Any]

# ═══════════════════════════════════════════════════════════
# Analysis Logic (from gui_cluster_v2.py)
# ═══════════════════════════════════════════════════════════
def get_data_source(version: str, version_mapping: Dict[str, str]) -> dict:
    """Get the correct data source based on version mapping"""
    source = version_mapping.get(version, 'GT')
    if source == 'GT':
        return data_store.gt_data
    else:
        return data_store.pred_data

def filter_data(data: dict, genre: str, emotion: str):
    """Filter data by genre and emotion (multi-label support)"""
    genres = data['genres']
    emotions = data['emotions']
    embeddings = data['embeddings']
    ids = data['ids']
    
    # Multi-label emotion matching
    mask = np.array([
        (g == genre) and (emotion in str(e)) 
        for g, e in zip(genres, emotions)
    ])
    
    return {
        'embeddings': embeddings[mask],
        'ids': ids[mask],
        'mask': mask
    }

def run_pca(embeddings: np.ndarray):
    """Run PCA to reduce to 2D"""
    if len(embeddings) < 2:
        return None, None
    
    pca = PCA(n_components=2)
    coords = pca.fit_transform(embeddings)
    return coords, pca

def find_best_k(coords: np.ndarray, k_range=(2, 6)):
    """Auto-detect best K using silhouette score"""
    if len(coords) < k_range[0]:
        return 2, []
    
    scores = []
    for k in range(k_range[0], min(k_range[1] + 1, len(coords))):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(coords)
            score = silhouette_score(coords, labels)
            scores.append({'k': k, 'score': round(score, 4)})
        except:
            scores.append({'k': k, 'score': 0})
    
    if not scores:
        return 2, []
    
    best = max(scores, key=lambda x: x['score'])
    return best['k'], scores

def run_kmeans(coords: np.ndarray, k: int):
    """Run K-Means clustering"""
    if len(coords) < k:
        k = max(2, len(coords))
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)
    centers = kmeans.cluster_centers_
    
    return labels, centers

def find_cluster_reps(coords: np.ndarray, labels: np.ndarray, ids: np.ndarray, centers: np.ndarray):
    """Find representative song for each cluster (closest to center)"""
    reps = []
    for i, center in enumerate(centers):
        cluster_mask = labels == i
        cluster_coords = coords[cluster_mask]
        cluster_ids = ids[cluster_mask]
        
        if len(cluster_coords) == 0:
            continue
        
        # Find closest to center
        distances = np.linalg.norm(cluster_coords - center, axis=1)
        closest_idx = np.argmin(distances)
        
        # Use representative song's coordinates (not center)
        rep_coords = cluster_coords[closest_idx]
        reps.append({
            'cluster': i,
            'id': str(cluster_ids[closest_idx]),
            'x': float(rep_coords[0]),
            'y': float(rep_coords[1])
        })
    
    return reps

def analyze_axis(pc_values: np.ndarray, song_ids: np.ndarray, lang: str = 'en'):
    """Calculate correlation between PC and audio features"""
    if data_store.features_df is None:
        return []
    
    # Get lang index for AXIS_MAPPING
    lang_idx = {'en': 0, 'zh': 1, 'ja': 2}.get(lang, 0)
    low_idx = 3 + lang_idx
    high_idx = 6 + lang_idx
    
    # Filter features to matching songs
    song_ids_str = [str(s) for s in song_ids]
    subset_df = data_store.features_df[data_store.features_df['id'].isin(song_ids_str)]
    
    # Create id -> index mapping
    id_to_idx = {str(sid): i for i, sid in enumerate(song_ids)}
    subset_df = subset_df.copy()
    subset_df['_order'] = subset_df['id'].map(id_to_idx)
    subset_df = subset_df.dropna(subset=['_order'])
    subset_df = subset_df.sort_values('_order')
    
    if len(subset_df) < 3:
        return []
    
    # Align pc_values
    valid_indices = subset_df['_order'].astype(int).values
    pc_aligned = pc_values[valid_indices]
    
    correlations = []
    feature_cols = [col for col in subset_df.columns if col not in ['id', 'error', '_order']]
    
    for feature_name in feature_cols:
        if feature_name not in AXIS_MAPPING:
            continue
        
        feature_values = subset_df[feature_name].values
        if np.isnan(feature_values).any():
            continue
        
        try:
            r, p_value = pearsonr(pc_aligned, feature_values)
            mapping = AXIS_MAPPING[feature_name]
            correlations.append({
                'feature': feature_name,
                'label': mapping[lang_idx],
                'low': mapping[low_idx],
                'high': mapping[high_idx],
                'r': round(r, 3),
                'abs_r': round(abs(r), 3)
            })
        except:
            continue
    
    # Sort by |r|
    correlations.sort(key=lambda x: x['abs_r'], reverse=True)
    return correlations

def get_best_label(correlations: list, threshold: float = CORRELATION_THRESHOLD, diff_threshold: float = DIFF_THRESHOLD):
    """Get best label(s) for axis interpretation"""
    if not correlations:
        return None, None, []
    
    # Filter by threshold
    valid = [c for c in correlations if c['abs_r'] >= threshold]
    if not valid:
        return None, None, []
    
    # Find features with similar correlation (within diff_threshold of top)
    top_r = valid[0]['abs_r']
    similar = [c for c in valid if (top_r - c['abs_r']) <= diff_threshold]
    
    # Combine labels and polarity
    labels = [c['label'] for c in similar]
    
    # Get polarity based on sign of r
    if similar[0]['r'] > 0:
        low_words = [c['low'] for c in similar]
        high_words = [c['high'] for c in similar]
    else:
        low_words = [c['high'] for c in similar]
        high_words = [c['low'] for c in similar]
    
    combined_label = ' / '.join(labels)
    
    return combined_label, round(top_r, 2), {
        'low': '\n'.join(low_words),
        'high': '\n'.join(high_words),
        'features': [c['feature'] for c in similar]
    }

# ═══════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════
@app.get("/api/info")
async def get_info():
    """Get available genres and emotions"""
    if not data_store.loaded or data_store.gt_data is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    genres = sorted(set(data_store.gt_data['genres']))
    
    # Parse multi-label emotions
    all_emotions = set()
    for emo_str in data_store.gt_data['emotions']:
        if emo_str and emo_str != 'Unknown':
            for emo in str(emo_str).split(','):
                all_emotions.add(emo.strip())
    
    return {
        'genres': list(genres),
        'emotions': sorted(all_emotions)
    }

@app.post("/api/analyze")
async def analyze(req: AnalysisRequest):
    """Run analysis for given genre/emotion/version"""
    if not data_store.loaded:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Get correct data source
    data = get_data_source(req.version, req.version_mapping)
    if data is None:
        raise HTTPException(status_code=500, detail="Data source not available")
    
    # Filter data
    filtered = filter_data(data, req.genre, req.emotion)
    embeddings = filtered['embeddings']
    ids = filtered['ids']
    
    if len(embeddings) < 3:
        return {
            'error': f'Too few songs ({len(embeddings)}). Need at least 3.',
            'count': len(embeddings)
        }
    
    # Run PCA
    coords, pca = run_pca(embeddings)
    if coords is None:
        return {'error': 'PCA failed', 'count': len(embeddings)}
    
    # Determine K
    if req.auto_k:
        best_k, k_scores = find_best_k(coords)
    else:
        best_k = req.manual_k
        k_scores = []
    
    # Run K-Means
    labels, centers = run_kmeans(coords, best_k)
    
    # Find cluster representatives
    cluster_reps = find_cluster_reps(coords, labels, ids, centers)
    
    # Analyze axes for all languages
    x_corr_en = analyze_axis(coords[:, 0], ids, 'en')
    y_corr_en = analyze_axis(coords[:, 1], ids, 'en')
    x_corr_zh = analyze_axis(coords[:, 0], ids, 'zh')
    y_corr_zh = analyze_axis(coords[:, 1], ids, 'zh')
    x_corr_ja = analyze_axis(coords[:, 0], ids, 'ja')
    y_corr_ja = analyze_axis(coords[:, 1], ids, 'ja')
    
    # Get best labels for all languages
    x_label_en, x_r, x_polarity_en = get_best_label(x_corr_en)
    y_label_en, y_r, y_polarity_en = get_best_label(y_corr_en)
    x_label_zh, _, x_polarity_zh = get_best_label(x_corr_zh)
    y_label_zh, _, y_polarity_zh = get_best_label(y_corr_zh)
    x_label_ja, _, x_polarity_ja = get_best_label(x_corr_ja)
    y_label_ja, _, y_polarity_ja = get_best_label(y_corr_ja)
    
    # Prepare point data
    colors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']
    points = []
    for i, (coord, song_id, label) in enumerate(zip(coords, ids, labels)):
        points.append({
            'id': str(song_id),
            'x': float(coord[0]),
            'y': float(coord[1]),
            'cluster': int(label),
            'color': colors[int(label) % len(colors)]
        })
    
    return {
        'count': len(embeddings),
        'k': best_k,
        'k_scores': k_scores,
        'points': points,
        'cluster_reps': cluster_reps,
        'axis': {
            'x': {
                'label': {
                    'en': x_label_en or 'PC1',
                    'zh': x_label_zh or 'PC1',
                    'ja': x_label_ja or 'PC1'
                },
                'r': x_r,
                'polarity': {
                    'en': x_polarity_en or {'low': '', 'high': ''},
                    'zh': x_polarity_zh or {'low': '', 'high': ''},
                    'ja': x_polarity_ja or {'low': '', 'high': ''}
                }
            },
            'y': {
                'label': {
                    'en': y_label_en or 'PC2',
                    'zh': y_label_zh or 'PC2',
                    'ja': y_label_ja or 'PC2'
                },
                'r': y_r,
                'polarity': {
                    'en': y_polarity_en or {'low': '', 'high': ''},
                    'zh': y_polarity_zh or {'low': '', 'high': ''},
                    'ja': y_polarity_ja or {'low': '', 'high': ''}
                }
            }
        },
        'correlations': {
            'x': x_corr_en[:5],
            'y': y_corr_en[:5]
        }
    }

@app.post("/api/submit")
async def submit(req: SubmitRequest):
    """Submit session data"""
    try:
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = req.session_data.get('userId', 'unknown')
        filename = f"session_{timestamp}_{user_id[:8]}.json"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(req.session_data, f, ensure_ascii=False, indent=2)
        
        return {'success': True, 'filename': filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/music/url")
async def get_music_url(id: str):
    """Proxy to get music URL from NetEase API"""
    # This would proxy to the actual NetEase API
    # For now, return a placeholder
    return {
        'id': id,
        'url': f"https://neon.zeabur.app/api/music/url?id={id}"
    }

# ═══════════════════════════════════════════════════════════
# Static File Serving (Vue SPA)
# ═══════════════════════════════════════════════════════════
# Path to Vue build output
DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "dist")

# Serve static assets (js, css, etc.)
if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

# SPA fallback - serve index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve Vue SPA for all non-API routes"""
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not built. Run 'npm run build' first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
