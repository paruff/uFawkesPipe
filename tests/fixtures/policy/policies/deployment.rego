package main

# Fixture for the reusables self-test: a Deployment must say it runs as non-root.
deny contains msg if {
	input.kind == "Deployment"
	not input.spec.template.spec.securityContext.runAsNonRoot
	msg := sprintf("Deployment %s must set securityContext.runAsNonRoot", [input.metadata.name])
}
