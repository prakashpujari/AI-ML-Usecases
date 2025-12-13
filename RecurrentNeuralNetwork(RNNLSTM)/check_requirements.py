required = [
    ('streamlit', 'streamlit'),
    ('pandas', 'pandas'),
    ('numpy', 'numpy'),
    ('sklearn', 'scikit-learn'),
    ('tensorflow', 'tensorflow'),
    ('matplotlib', 'matplotlib'),
    ('plotly', 'plotly'),
]

missing = []

for mod_name, pkg_name in required:
    try:
        __import__(mod_name)
        print(f"OK: {pkg_name}")
    except Exception as e:
        print(f"MISSING: {pkg_name} -> {e.__class__.__name__}: {e}")
        missing.append(pkg_name)

if missing:
    print("\nSome packages are missing. Install them with:")
    print("pip install " + " ".join(missing))
else:
    print('\nAll required packages are installed.')
