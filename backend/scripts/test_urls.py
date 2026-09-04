import urllib.request

urls = [
    ("det_10g", "https://huggingface.co/public-data/insightface/resolve/main/models/buffalo_l/det_10g.onnx"),
    ("codeformer_pth", "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth"),
    ("bisenet_pth", "https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/parsing_bisenet.pth"),
    ("codeformer_onnx", "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/codeformer.onnx"),
    ("codeformer_spyk", "https://huggingface.co/spyk/codeformer/resolve/main/codeformer.onnx"),
    ("gpen_onnx", "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GPEN-BFR-512.onnx"),
]

headers = {"User-Agent": "Mozilla/5.0"}

for name, url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            size_mb = int(r.info().get("Content-Length", 0)) / (1024 * 1024)
            print(f"[OK] {name}: {r.status} ({size_mb:.2f} MB)")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
