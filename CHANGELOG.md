# Changelog

All notable changes to uFawkesPipe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.17.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.16.0-beta.1...v1.17.0-beta.1) (2026-10-25)


### Added

* **ci-image:** add syft, conftest, cosign for supply-chain reusables ([#188](https://github.com/paruff/uFawkesPipe/issues/188)) ([040b9ce](https://github.com/paruff/uFawkesPipe/commit/040b9ce929498248eaee95d8d246ddddc7f3fb0a))
* **ci-image:** add the Terraform and Kubernetes tools fawkes needs ([#186](https://github.com/paruff/uFawkesPipe/issues/186)) ([2d68d1b](https://github.com/paruff/uFawkesPipe/commit/2d68d1b473d2bf957e8196c3434bab081cfb2059))


### Fixed

* **ci-image:** bump actions-runner, docker-cli and compose for fixed CVEs ([#197](https://github.com/paruff/uFawkesPipe/issues/197)) ([76568cd](https://github.com/paruff/uFawkesPipe/commit/76568cd81c9d586a61d1dd86ee72dddf1a111464))
* **ci-image:** bump certifi to 2026.10.19 for GHSA-6q48-6c7w-9gw2 ([#198](https://github.com/paruff/uFawkesPipe/issues/198)) ([1d5de8a](https://github.com/paruff/uFawkesPipe/commit/1d5de8a84bdb566ea1dda8493515cd3d0ac62d47))


### Docs

* **readme:** cite research basis (paruff/uFawkes.dev[#65](https://github.com/paruff/uFawkesPipe/issues/65)) ([#190](https://github.com/paruff/uFawkesPipe/issues/190)) ([856d36a](https://github.com/paruff/uFawkesPipe/commit/856d36a4e333a05e20b8c5c7ca09e3f3246177f5))
* **review:** REVIEW.md and the Project 7 workflow ([#200](https://github.com/paruff/uFawkesPipe/issues/200)) ([6905653](https://github.com/paruff/uFawkesPipe/commit/69056534c9bf006f19f61a6726a4a6b1bf2c5cbf))


### Chores

* **ci-image:** build ufawkes-ci on fawkes-core 2.2.0 ([#196](https://github.com/paruff/uFawkesPipe/issues/196)) ([6dfccae](https://github.com/paruff/uFawkesPipe/commit/6dfccae0ec8617c65a8b11eef74ac25a5db5e284))
* **deps:** bump actions/setup-node from 7.0.0 to 7.1.0 ([#192](https://github.com/paruff/uFawkesPipe/issues/192)) ([e703fdd](https://github.com/paruff/uFawkesPipe/commit/e703fddafd146a9b19e024d61253d0af190ab61c))
* **deps:** bump actions/upload-artifact from 7.0.1 to 7.0.2 ([#191](https://github.com/paruff/uFawkesPipe/issues/191)) ([fb125b7](https://github.com/paruff/uFawkesPipe/commit/fb125b7d5e5b418928af2d7d40b4c1eb7a7eecd1))
* **deps:** bump github/codeql-action/upload-sarif ([#194](https://github.com/paruff/uFawkesPipe/issues/194)) ([7873457](https://github.com/paruff/uFawkesPipe/commit/787345713985224b57205141fd00fa6cf6b13be2))
* **deps:** bump github/codeql-action/upload-sarif ([#199](https://github.com/paruff/uFawkesPipe/issues/199)) ([53cb24a](https://github.com/paruff/uFawkesPipe/commit/53cb24a1bc4a49be216671442671a3ffa7d932ae))
* **deps:** bump trufflesecurity/trufflehog from 3.98.0 to 3.99.2 ([#193](https://github.com/paruff/uFawkesPipe/issues/193)) ([3759b8e](https://github.com/paruff/uFawkesPipe/commit/3759b8eb3219decc22ac013c8926f120c6e0d4fb))
* **infra:** adopt the OpenCode shift-left plugin ([#153](https://github.com/paruff/uFawkesPipe/issues/153)) ([#189](https://github.com/paruff/uFawkesPipe/issues/189)) ([a4079d9](https://github.com/paruff/uFawkesPipe/commit/a4079d905cbe12a5612a245ad9bd2eb90de04842))

## [1.16.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.15.1-beta.1...v1.16.0-beta.1) (2026-10-12)


### Added

* **ci:** scan container images in reusable-security-scanning ([#184](https://github.com/paruff/uFawkesPipe/issues/184)) ([9903ac7](https://github.com/paruff/uFawkesPipe/commit/9903ac7f5c6685bd10ea763ae98645aa0d3409d9))


### Fixed

* **ci-image:** stop find|grep -q failing the build under pipefail ([#182](https://github.com/paruff/uFawkesPipe/issues/182)) ([9b2c25d](https://github.com/paruff/uFawkesPipe/commit/9b2c25d3a49e6b514a991e3f61887759b7a61548))

## [1.15.1-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.15.0-beta.1...v1.15.1-beta.1) (2026-10-12)


### Chores

* **ci:** call the released reusables at v1.15.0-beta.1 ([#181](https://github.com/paruff/uFawkesPipe/issues/181)) ([#181](https://github.com/paruff/uFawkesPipe/issues/181)) ([110a55d](https://github.com/paruff/uFawkesPipe/commit/110a55d0b8bcc617228e0458344269f1a49203d5))

## [1.15.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.14.0-beta.1...v1.15.0-beta.1) (2026-10-12)


### Added

* **ci-image:** record the fawkes-core digest; add pipe-ci release-match ([#178](https://github.com/paruff/uFawkesPipe/issues/178)) ([1d6309b](https://github.com/paruff/uFawkesPipe/commit/1d6309b0ce23f4a61e550a8bb81f626a3b19cf78))
* **ci:** check CI image and devcontainer are from one release ([#180](https://github.com/paruff/uFawkesPipe/issues/180)) ([cc2c171](https://github.com/paruff/uFawkesPipe/commit/cc2c171f2db533ece05355ce586f85040e302cbc))
* **ci:** run pre-flight's hook stages in the digest-pinned CI image ([#176](https://github.com/paruff/uFawkesPipe/issues/176)) ([f2ccc88](https://github.com/paruff/uFawkesPipe/commit/f2ccc88f5c715259259bce7e67c1c4040e3924c3))


### Docs

* **ci:** the released reusables' contract; scripts/suite-bump.sh ([#179](https://github.com/paruff/uFawkesPipe/issues/179)) ([b78bd82](https://github.com/paruff/uFawkesPipe/commit/b78bd824a80df470042d1ffbf33a595ae1ee43bf))

## [1.14.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.13.1-beta.1...v1.14.0-beta.1) (2026-10-12)


### Added

* **ci-image:** ufawkes-ci image with verified fetch, semgrep, runner and pipe-ci (PR A of [#166](https://github.com/paruff/uFawkesPipe/issues/166)) ([#170](https://github.com/paruff/uFawkesPipe/issues/170)) ([bcb03f4](https://github.com/paruff/uFawkesPipe/commit/bcb03f4a358dceacf17a26fb37945ff753b47aa1))
* **ci:** dispatch-gated runner input for reusable pre-flight ([#171](https://github.com/paruff/uFawkesPipe/issues/171)) ([ea5ef23](https://github.com/paruff/uFawkesPipe/commit/ea5ef232e49dc1667142400326a473f1e32e743c))
* **ci:** publish ufawkes-ci image with signing and gates ([#172](https://github.com/paruff/uFawkesPipe/issues/172)) ([b47e8b0](https://github.com/paruff/uFawkesPipe/commit/b47e8b017266932a529cdbcaf6892b02cd86dbb6))


### Fixed

* **ci-image:** gate what the image adds, report fawkes-core's findings ([#175](https://github.com/paruff/uFawkesPipe/issues/175)) ([634c8ad](https://github.com/paruff/uFawkesPipe/commit/634c8add503be11a16c9ebef856496aa604e8d2a))
* **ci:** stop the nim-proxy with docker rm -f instead of || true ([#180](https://github.com/paruff/uFawkesPipe/issues/180)) ([#168](https://github.com/paruff/uFawkesPipe/issues/168)) ([bd29634](https://github.com/paruff/uFawkesPipe/commit/bd29634985cbd78128cc80ce2e75819218e807fe))


### Chores

* **deps:** bump trufflesecurity/trufflehog from 3.97.9 to 3.98.0 ([#174](https://github.com/paruff/uFawkesPipe/issues/174)) ([129c58a](https://github.com/paruff/uFawkesPipe/commit/129c58ace20e8b1061ed41327f231dd441978191))

## [1.13.1-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.13.0-beta.1...v1.13.1-beta.1) (2026-10-10)


### Fixed

* **ci:** remove silent passes from the security and coverage gates ([#180](https://github.com/paruff/uFawkesPipe/issues/180)) ([#167](https://github.com/paruff/uFawkesPipe/issues/167)) ([c9c7b3b](https://github.com/paruff/uFawkesPipe/commit/c9c7b3bf9fc10e059a2ed66a31d573ef6e62d1b0))
* **templates:** repair issue-form schema and PR gate commands ([#164](https://github.com/paruff/uFawkesPipe/issues/164)) ([8c8595a](https://github.com/paruff/uFawkesPipe/commit/8c8595a9e3a220cb7b03b639423d07ff67c3345b))


### Docs

* **issue-templates:** add bug_report, feature, security templates ([#161](https://github.com/paruff/uFawkesPipe/issues/161)) ([aafadf4](https://github.com/paruff/uFawkesPipe/commit/aafadf41da9fc65317244d5bc267e87d37a610a3))
* **pr-template:** add standardized PR template ([#160](https://github.com/paruff/uFawkesPipe/issues/160)) ([0e0f21a](https://github.com/paruff/uFawkesPipe/commit/0e0f21a26b1a0d5e68cc00ab25efdfc7b782e0a7))


### Chores

* **templates:** drop dangling label references from issue templates ([#163](https://github.com/paruff/uFawkesPipe/issues/163)) ([88c908a](https://github.com/paruff/uFawkesPipe/commit/88c908aba37caef2feff0317b45f411ae1fe9870))

## [1.13.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.12.0-beta.1...v1.13.0-beta.1) (2026-10-07)


### Added

* **shift-left:** keep Pipe's own clones in step with its hook config ([#157](https://github.com/paruff/uFawkesPipe/issues/157)) ([ca66c85](https://github.com/paruff/uFawkesPipe/commit/ca66c850563af9da2b83f3c869b305cc8c504d1e))

## [1.12.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.11.1-beta.1...v1.12.0-beta.1) (2026-10-07)


### Added

* **shift-left:** doctor D7 and the OpenCode plugin ([#149](https://github.com/paruff/uFawkesPipe/issues/149)) ([09ba84f](https://github.com/paruff/uFawkesPipe/commit/09ba84f84ef8cd4fae0f4646e81b87b5ccdfe2cf))
* **shift-left:** lint Pipe's own workflows and config schemas ([#151](https://github.com/paruff/uFawkesPipe/issues/151)) ([46d5e41](https://github.com/paruff/uFawkesPipe/commit/46d5e419cdd99d80ad002024fec8c31efbfde674))
* **shift-left:** reinstall git hooks when the hook config adds a stage ([#154](https://github.com/paruff/uFawkesPipe/issues/154)) ([312fa48](https://github.com/paruff/uFawkesPipe/commit/312fa4870b698081fb5d4bd96c48e91be04faf74))
* **types:** type-check Pipe's Python script and OpenCode plugin ([#153](https://github.com/paruff/uFawkesPipe/issues/153)) ([80d4f36](https://github.com/paruff/uFawkesPipe/commit/80d4f366cec3afe5e90e3d731f8dc9de37f93cad))


### Docs

* **ci-runner-image:** add ufawkes-ci implementation plan ([#156](https://github.com/paruff/uFawkesPipe/issues/156)) ([ef719be](https://github.com/paruff/uFawkesPipe/commit/ef719bedd0b9ebc8ae5dfc942e6ace89691b2b7a))
* **ci-runner-image:** add ufawkes-ci runner image spec ([#146](https://github.com/paruff/uFawkesPipe/issues/146)) ([3033420](https://github.com/paruff/uFawkesPipe/commit/3033420852f2c51336df8e5109ebd0fa86d5f4cf))
* **ci-runner-image:** resolve OQ1 - bake semgrep in the CI layer ([#148](https://github.com/paruff/uFawkesPipe/issues/148)) ([2a62c5c](https://github.com/paruff/uFawkesPipe/commit/2a62c5c27295ab5158fafde01ac7c9612e3009a0))

## [1.11.1-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.11.0-beta.1...v1.11.1-beta.1) (2026-10-04)


### Fixed

* **shift-left:** parity counts a single-hook CI run for that hook only (P6) ([#143](https://github.com/paruff/uFawkesPipe/issues/143)) ([9732fe1](https://github.com/paruff/uFawkesPipe/commit/9732fe18d211cbbe3a15f2e649adbeef175edd99))

## [1.11.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.10.0-beta.1...v1.11.0-beta.1) (2026-10-04)


### Added

* **shift-left:** uFawkesPipe runs its own shift-left hooks (P5a) ([#142](https://github.com/paruff/uFawkesPipe/issues/142)) ([acc95ef](https://github.com/paruff/uFawkesPipe/commit/acc95eff323748cef9ae18451d17b814d36132c4))


### Fixed

* **ci:** clear what Pipe's first SAST and pin checks find (P5b) ([#140](https://github.com/paruff/uFawkesPipe/issues/140)) ([64a8ca1](https://github.com/paruff/uFawkesPipe/commit/64a8ca180d75f9377d52e4917b4f9f5dae952f26))

## [1.10.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.9.0-beta.1...v1.10.0-beta.1) (2026-10-04)


### Added

* **shift-left:** the semgrep hook, pinned and pip-installable (P3) ([#136](https://github.com/paruff/uFawkesPipe/issues/136)) ([483697a](https://github.com/paruff/uFawkesPipe/commit/483697a1ae0ce4fd191c088b64e8d924967e8162))


### Fixed

* **shift-left:** stop git maintenance racing the doctor tests' copies ([#139](https://github.com/paruff/uFawkesPipe/issues/139)) ([8c2631f](https://github.com/paruff/uFawkesPipe/commit/8c2631f943b996b8f3daf186fa48bc85833e536c))

## [1.9.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.8.3-beta.1...v1.9.0-beta.1) (2026-10-04)


### Added

* **shift-left:** publish the suite's shift-left hooks and consumer shim (P1) ([#132](https://github.com/paruff/uFawkesPipe/issues/132)) ([9214b4d](https://github.com/paruff/uFawkesPipe/commit/9214b4da2060d5c1f6e0ba5388c4f2beb036b92f))
* **shift-left:** the agent gate, hooks before an agent stops (P2a) ([#134](https://github.com/paruff/uFawkesPipe/issues/134)) ([4660c24](https://github.com/paruff/uFawkesPipe/commit/4660c242f2a5b1ff417e79af27fbb07dcce34a83))
* **shift-left:** the doctor, know when checks aren't running (P2b) ([#135](https://github.com/paruff/uFawkesPipe/issues/135)) ([9943655](https://github.com/paruff/uFawkesPipe/commit/994365529015586565b8581ca4f40e929fa0ef2d))

## [1.8.3-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.8.2-beta.1...v1.8.3-beta.1) (2026-10-03)


### Chores

* **devcontainer:** declare hostRequirements (2 CPUs, 4 GB) ([#130](https://github.com/paruff/uFawkesPipe/issues/130)) ([b1b0446](https://github.com/paruff/uFawkesPipe/commit/b1b044639f768a8cd7b97e796c8c39d39f32c867))

## [1.8.2-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.8.1-beta.1...v1.8.2-beta.1) (2026-10-03)


### Chores

* **devcontainer:** use the shared fawkes-space CDE (2.0.0-rc.1) ([#127](https://github.com/paruff/uFawkesPipe/issues/127)) ([79d14af](https://github.com/paruff/uFawkesPipe/commit/79d14afd465c18afd7f1516a7c64ba051812c71b))

## [1.8.1-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.8.0-beta.1...v1.8.1-beta.1) (2026-10-03)


### Docs

* **design:** point to the suite design reference ([#124](https://github.com/paruff/uFawkesPipe/issues/124)) ([588489a](https://github.com/paruff/uFawkesPipe/commit/588489afa22cb322dba2fafad437609c5598715b))
* stop naming retired planes and Jenkins as current in the README ([#116](https://github.com/paruff/uFawkesPipe/issues/116)) ([5081ba0](https://github.com/paruff/uFawkesPipe/commit/5081ba0d7d876deb1101634cc2dbb348fbec81ea))

## [1.8.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.7.4-beta.1...v1.8.0-beta.1) (2026-10-02)


### Added

* **ci:** unified pre-commit, unit-test suites, ruff config, harness parity ([#104](https://github.com/paruff/uFawkesPipe/issues/104)) ([a4a8b37](https://github.com/paruff/uFawkesPipe/commit/a4a8b3710d25acffb90585e6436b2d4dd1aa9ddf))
* **devcontainer:** use unified GHCR image ghcr.io/paruff/ufawkesai-devcontainer:latest ([#106](https://github.com/paruff/uFawkesPipe/issues/106)) ([7167fbc](https://github.com/paruff/uFawkesPipe/commit/7167fbcaaaefd8724f55eeb4ce2110e986dab203))


### Fixed

* **ci:** check only pushed commits in the push-time format check ([#109](https://github.com/paruff/uFawkesPipe/issues/109)) ([336143e](https://github.com/paruff/uFawkesPipe/commit/336143e97b29ed56a7d272508e0c28232a6406df))
* **ci:** main-ci-guard skips cancelled/skipped runs on main ([#107](https://github.com/paruff/uFawkesPipe/issues/107)) ([b71b8da](https://github.com/paruff/uFawkesPipe/commit/b71b8da36353bf4de534ce2e8bf7709e39c22c96))


### Chores

* **agents:** use the shared uFawkesAI agents instead of local copies ([#108](https://github.com/paruff/uFawkesPipe/issues/108)) ([4f892f2](https://github.com/paruff/uFawkesPipe/commit/4f892f2b817bd22989812725681df7e7d5eae6d3))

## [1.7.4-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.7.3-beta.1...v1.7.4-beta.1) (2026-09-28)


### Fixed

* **suite:** sync 4 agents, hooks, model routing from uFawkesAI template ([#102](https://github.com/paruff/uFawkesPipe/issues/102)) ([d8f2031](https://github.com/paruff/uFawkesPipe/commit/d8f203188d4d644136fd557c7f9231fd028d49e0))

## [1.7.3-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.7.2-beta.1...v1.7.3-beta.1) (2026-09-28)


### Docs

* finish uFawkesRes/fawkes corrections in README and AGENTS.md ([#100](https://github.com/paruff/uFawkesPipe/issues/100)) ([2c5ee29](https://github.com/paruff/uFawkesPipe/commit/2c5ee292d153ee751adb5709f31187c0a8769df2)), closes [#97](https://github.com/paruff/uFawkesPipe/issues/97)

## [1.7.2-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.7.1-beta.1...v1.7.2-beta.1) (2026-09-27)


### Docs

* add INTENT.md; mark suite mode's uFawkesRes dependency unsupported ([#98](https://github.com/paruff/uFawkesPipe/issues/98)) ([a6a6a9b](https://github.com/paruff/uFawkesPipe/commit/a6a6a9ba97387771a1b91b1bbd2e7eecf8f4e7ef)), closes [#96](https://github.com/paruff/uFawkesPipe/issues/96)


### Chores

* **deps:** bump trufflesecurity/trufflehog from 3.97.4 to 3.97.6 ([#95](https://github.com/paruff/uFawkesPipe/issues/95)) ([00780ce](https://github.com/paruff/uFawkesPipe/commit/00780ce7b81c44c6379deacc8a8a7cd7b09eb29d))

## [1.7.1-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.7.0-beta.1...v1.7.1-beta.1) (2026-09-19)


### Chores

* stop tracking graphify-out/ ([#93](https://github.com/paruff/uFawkesPipe/issues/93)) ([554a16d](https://github.com/paruff/uFawkesPipe/commit/554a16d54ebbba747c111af8371ce60122e828ac))

## [1.7.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.6.0-beta.1...v1.7.0-beta.1) (2026-09-19)


### Added

* **woodpecker:** persistent Maven cache for the CI agent ([#91](https://github.com/paruff/uFawkesPipe/issues/91)) ([13cf78b](https://github.com/paruff/uFawkesPipe/commit/13cf78baecd8ed11d70203ac07261ef15a847e1d))


### Fixed

* **generator:** Java 21 test image + consistent build image reference ([#90](https://github.com/paruff/uFawkesPipe/issues/90)) ([0271408](https://github.com/paruff/uFawkesPipe/commit/0271408620337cc9cc5ba28ed6d3ea298e7ced21))

## [1.6.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.5.0-beta.1...v1.6.0-beta.1) (2026-09-18)


### Added

* **observability:** wire OTEL, Alloy logs, DefectDojo ingestion ([#88](https://github.com/paruff/uFawkesPipe/issues/88)) ([51537bd](https://github.com/paruff/uFawkesPipe/commit/51537bda6240a8872cf4ebb2c16ee4fd9677ec55))

## [1.5.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.4.0-beta.1...v1.5.0-beta.1) (2026-09-16)


### Added

* **security:** add deploy stage + bootstrap-secrets + Bandit/DAST + ShellCheck fixes ([#86](https://github.com/paruff/uFawkesPipe/issues/86)) ([33f8d98](https://github.com/paruff/uFawkesPipe/commit/33f8d980348a29da174c93172485dc0f3cff38e0))

## [1.4.0-beta.1](https://github.com/paruff/uFawkesPipe/compare/v1.3.0-beta.1...v1.4.0-beta.1) (2026-09-15)


### Added

* **ci:** add release-please, pin opencode-ai off [@latest](https://github.com/latest) ([#78](https://github.com/paruff/uFawkesPipe/issues/78)) ([b3c504f](https://github.com/paruff/uFawkesPipe/commit/b3c504fd90454821e02138242deaeeb5425ba12e))
* **docs:** host shared DORA event contracts, sourced from uFawkesObs ([#69](https://github.com/paruff/uFawkesPipe/issues/69)) ([d399061](https://github.com/paruff/uFawkesPipe/commit/d39906149a9971c89e6da4b083c2ca827d7c9051))
* **planning:** add 4-tier planning cascade (VISION, MILESTONES, EXECUTION_QUEUE, plan-for-the-day) ([#82](https://github.com/paruff/uFawkesPipe/issues/82)) ([76e5457](https://github.com/paruff/uFawkesPipe/commit/76e5457895903cb8e49dbb56f4d8675b3c09d964))
* **security:** add Bandit SAST and ZAP DAST to pipeline contract ([#84](https://github.com/paruff/uFawkesPipe/issues/84)) ([4b96cba](https://github.com/paruff/uFawkesPipe/commit/4b96cba098b3613496da230336e771e228459d48))


### Fixed

* **ci:** allow external_directory writes for opencode ([#73](https://github.com/paruff/uFawkesPipe/issues/73)) ([32326eb](https://github.com/paruff/uFawkesPipe/commit/32326eb059dac2c0431853cb8cc0619986082037))
* **dora:** send deployment events to uFawkesObs REST /event endpoint ([#70](https://github.com/paruff/uFawkesPipe/issues/70)) ([9a9b8b8](https://github.com/paruff/uFawkesPipe/commit/9a9b8b8e2fdb3423ecb8fc1dd1b8e9c9465e2298))


### Docs

* document never-swallow-exceptions principle in coding standards ([#72](https://github.com/paruff/uFawkesPipe/issues/72)) ([6fc8ab0](https://github.com/paruff/uFawkesPipe/commit/6fc8ab0109663f55b21ecbf849902a0e6ca427dc))
* **dora:** document OTLP telemetry contract, add commit-format guidance ([#71](https://github.com/paruff/uFawkesPipe/issues/71)) ([7f5a090](https://github.com/paruff/uFawkesPipe/commit/7f5a09052360b0579646dbc63d5aca59aefe386e))


### Chores

* **deps:** bump actions/checkout from 4 to 7 ([#74](https://github.com/paruff/uFawkesPipe/issues/74)) ([4c9e618](https://github.com/paruff/uFawkesPipe/commit/4c9e618ded73c57fbe4d7e3c4fa0c71ffacb59b9))
* **deps:** bump actions/setup-node from 4 to 7 ([#75](https://github.com/paruff/uFawkesPipe/issues/75)) ([62fcf53](https://github.com/paruff/uFawkesPipe/commit/62fcf531a21a22c91d9bc68244d52fcdaad59a37))
* **deps:** bump googleapis/release-please-action from 4.4.1 to 5.0.0 ([#80](https://github.com/paruff/uFawkesPipe/issues/80)) ([84c647d](https://github.com/paruff/uFawkesPipe/commit/84c647d29ac45f539f17d16150eb3b1f829bd129))
* **deps:** bump hadolint/hadolint-action from 3.4.0 to 3.5.0 ([#77](https://github.com/paruff/uFawkesPipe/issues/77)) ([2a2e153](https://github.com/paruff/uFawkesPipe/commit/2a2e1534d1136cc13c0573657e484b9ba08a0dbf))
* **deps:** bump trufflesecurity/trufflehog from 3.97.0 to 3.97.1 ([#76](https://github.com/paruff/uFawkesPipe/issues/76)) ([fe0fcad](https://github.com/paruff/uFawkesPipe/commit/fe0fcad085ad19c1e50f3bacd2f3cddccb33169e))
* **deps:** bump trufflesecurity/trufflehog from 3.97.1 to 3.97.4 ([#81](https://github.com/paruff/uFawkesPipe/issues/81)) ([ccad93c](https://github.com/paruff/uFawkesPipe/commit/ccad93c72512713761637eeaf0553556f0a6c051))

## [1.3.0-beta.1] - 2026-08-10

### Added

- `.fawkespipe.yml` → `.woodpecker.yml` pipeline contract generator (`make generate-pipeline` / `make check-pipeline`), resolving beta blocker B-1 (PIPE-009, #64)
- GitOps lifecycle gates (#55)
- Pre-commit hook validation for conventional commits
- Pre-push hook running all pre-commit checks
- `make validate-agents` target for agent/skill validation
- `make fix-and-commit` target for automated formatting + commit
- GitHub Actions issue templates (bug_report, feature_request)
- METRICS.md documentation for DORA metrics collection
- `docs/BETA_RELEASE_PLAN.md` beta-readiness audit and action plan (#63)

### Changed

- Migrated remaining agent/skill definitions and scripts from Jenkins to Woodpecker CI (#60)
- Updated observability-agent for OTEL/DORA integration with uFawkesObs
- Updated pipeline-library-agent for Woodpecker pipeline definitions
- Updated security-agent for Woodpecker secret handling
- Updated smoke-test-agent for Woodpecker health endpoints
- Updated workflow-agent for GitHub Actions standards
- Updated pipeline-contract skill for Woodpecker config loading

### Removed

- Legacy `shared/vars/*.groovy` Jenkins shared library files
- Legacy `jenkins/` directory (JCasC, plugin lists, seed jobs)
- Legacy `docker-compose.yml` (Jenkins-based stack)
- Legacy `k8s/` manifests (Jenkins-based, superseded by `compose.yaml` + `.woodpecker.yml`)

### Fixed

- Pre-push hook argument handling (`pass_filenames: false`)
- Agent/skill validation warnings (applies globs, context references)
- Preflight job no longer fails when the PR-size comment lacks `issues:write` permission (#59)

## [1.2.0] - 2026-07-18

### Added

- `policy-check` pipeline step for Rego policy validation (#49)
- `generate-sbom` and `sign-image` supply-chain pipeline steps (#48)
- `make health` / `make health-suite` targets for container health status (#44)
- `reusable-main-ci-guard` and `reusable-rollback` GitHub Actions workflows (#54)

### Changed

- `allow-latest` input added for documented `:latest` image-tag exceptions (#43)

## [1.1.1] - 2026-07-02

### Added

- Automated golden-path acceptance test suite, AC-01–AC-14 (#42)
- `validate-agents` Woodpecker CI step (PIPE-008, #41)
- Staged pipeline restructure with consolidated test suites (WP-009, #37)
- `notify-obs` deployment event step (WP-006, #34)
- `upload-defectdojo` telemetry collector step (WP-005, #33)
- `vuln-scan-fs` / `vuln-scan-image` Trivy steps (WP-004, #31)
- `secrets-scan` (Gitleaks) hard-gate step (WP-003, #27)
- `fawkes-net` external network for suite mode (WP-002, #25)
- `ARCHITECTURE.md`, `KNOWN_LIMITATIONS.md`, `GOLDEN_PATH.md`, `MODEL_POLICY.md`, plus suite-mode compose (#24)
- uFawkesPipe v0.2 specification document (#23)

### Changed

- Agents/skills migrated from Jenkins to Woodpecker CI, plus Score integration (#30)
- README and `QUICKSTART.md` updated for the v0.2 Woodpecker CI stack (#35, #36)

### Fixed

- Pre-push guardrail added; pre-commit runs read-only in CI; flaky SBOM pre-check removed (#28, #29, #32)

## [1.1.0] - 2026-06-27

### Fixed

- Coverage-threshold enforcement and e2e test defaults added (#21)

## [1.0.0] - 2026-06-27

### Added

- GitHub Actions CI workflow for the repo itself (DY-002)

### Changed

- Renamed `deliveryd` → `uFawkesPipe` across identity, metadata, platform config, and K8s manifests
- Renamed pipeline contract file `.deliveryd.yml` → `.fawkespipe.yml`

### Fixed

- CI workflow failures, yamllint failures, invalid shellcheck action, Node.js 24 deprecation warning

## [0.3.0] - 2026-06-30

### Added

- Gitleaks secret scanning as hard gate in CI
- Woodpecker CI pipeline (`.woodpecker.yml`)
- Structured JSON logging for all pipeline steps
- DORA deployment event emission (`notify-obs` step)
- Suite mode with uFawkesRes + uFawkesObs integration
- SonarQube SAST integration
- Trivy vulnerability scanning (filesystem + image)
- OWASP Dependency-Check integration

### Changed

- CI/CD engine migrated from Jenkins to Woodpecker
- Pipeline contract renamed from `.deliveryd.yml` to `.fawkespipe.yml`
- Builder images updated to Paketo Buildpacks base
- Service labels standardized: `plane=ufawkespipe`, `managed-by=fawkes`

### Deprecated

- `.deliveryd.yml` contract filename (use `.fawkespipe.yml`)
- Jenkins-based pipeline definitions

## [0.2.0] - 2026-06-15

### Added

- Suite mode compose files (`compose.suite.yaml`)
- External network `fawkes-backbone-net` for uFawkesRes integration
- OTEL Collector integration for uFawkesObs
- Valkey cache service
- Authelia SSO integration
- Traefik ingress for suite mode

### Changed

- Architecture documentation updated
- Known limitations documented
- Golden path workflow documented

## [0.1.0] - 2026-06-01

### Added

- Initial uFawkesPipe release
- Jenkins-based CI/CD stack
- Pipeline contract specification
- Shared Groovy pipeline library
- Buildpack language packs (Java, Python, Node.js, Go)
- Docker Compose standalone deployment
- Basic security scanning (Trivy, Gitleaks)
