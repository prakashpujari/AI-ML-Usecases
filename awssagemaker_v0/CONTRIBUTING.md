## Contributing guidelines — model artifacts

This repository normally excludes large model artifacts from Git. The
project policy allows committing a single approved model file for
convenience: `Model/Train/model.joblib`.

Rules
- Keep the committed model file small (under ~50 MB) when possible.
- Only commit `Model/Train/model.joblib` when it's required for demos or
  smoke tests — avoid committing frequent training outputs.
- For larger artifacts or many model versions, use S3 or Git LFS instead
  of committing into the repository.

Recommended workflow
1. Train locally and validate your model.
2. If you need to include the model in the repo for a demo, add only the
   final artifact `Model/Train/model.joblib` and include a clear commit
   message describing the model provenance (date, training hyperparameters).
3. For reproducibility, also commit the training notebook or a short
   note describing the command used to create the artifact.

Git LFS suggestion (optional)
If model files grow larger than your preferred Git limits, enable Git LFS:

```bash
git lfs install
git lfs track "*.joblib"
git add .gitattributes
git commit -m "Enable LFS for joblib models"
```

Cleaning up large files
- Use `git rm --cached <file>` to remove a tracked file from the repo while
  leaving it on disk.

Contact
If you're unsure whether to commit an artifact, open an issue or ask for
advice.
