# Keeper evidence fail-closed verification

## Immutable pack passes

```text
$ python tools/verify_keeper_evidence.py docs/evidence/slate/manifest.json
PASS: docs/evidence/slate/manifest.json
keeper_count=11
artifact_count=48
manifest_sha256=5e3220dbce12bab2f792975abc96359e389b6af2a0b731731d6e6ede34f780cf
```

## Controlled one-byte mutation fails

The mutation is performed only in a temporary full copy. The committed evidence pack remains unchanged.

```text
$ python tools/verify_keeper_evidence.py /var/folders/7q/tx7m0tg12m5cgq7k8z8q2dzw0000gn/T/openjutsu-evidence-mutation-3udas1qa/slate/manifest.json
FAIL: /var/folders/7q/tx7m0tg12m5cgq7k8z8q2dzw0000gn/T/openjutsu-evidence-mutation-3udas1qa/slate/manifest.json
keeper[cameramove_jay_stretch].artifacts[3].sha256 changed
controlled_mutation_target=keepers/cameramove_jay_stretch/cameramove_jay_stretch_qwen.md
controlled_mutation=byte[-2] XOR 0x01
original_sha256=853edbf8b0a37fa46e7aec03bdc6302fdee5791189cfcef2a4482159288c6882
mutated_sha256=2df22b65b3ae39a29b6f011fdaca263428bcc0afb9cf66923e93f6afdde9f5e8
temporary_copy_deleted=true
committed_pack_sha256_unchanged=true
```
