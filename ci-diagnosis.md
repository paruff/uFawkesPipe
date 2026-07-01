Failure:      Build & Validate / Build & Validate, Validate Configs, Pipeline Complete
Location:     .github/workflows/ci-quality.yml:57-67, tests/unit/test_k8s_validation.py:26-28, Makefile:40-46, validate.sh:105-130
Evidence:     - kubeconform: "k8s/ - failed validation: lstat k8s/: no such file or directory"
              - pytest: "FAILED tests/unit/test_k8s_validation.py::TestK8sManifestsValidation::test_k8s_files_exist - AssertionError: No K8s manifests found in k8s/"
              - Coverage gate then failed because 1 test failure caused overall test run exit code 1
              - Pipeline Complete job then failed because Build & Validate was failure
Likely Cause: k8s/ directory and all Jenkins files were deleted in commit 9407ffb but CI workflows, tests, Makefile, and validate.sh still reference k8s/ path and Jenkins history files.
Confidence:   HIGH
Proposed Fix: Remove all k8s and Jenkins references from CI workflows, tests, Makefile, validate.sh, and conftest fixtures so they align with the deleted directories.
