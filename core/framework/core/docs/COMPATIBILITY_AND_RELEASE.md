# Compatibilidad y release

Core usa SemVer para package y contratos públicos. Un cambio incompatible de
schema, receipt, profile o API exige MAJOR. Una extensión compatible exige MINOR
y una corrección sin cambio de contrato exige PATCH.

La distribución local incluye un wheel PEP 517, export Foundation + Core,
checksum, SBOM y provenance. El backend PEP 517 vive en el proyecto, usa solo
stdlib y no descarga herramientas de build. Los gates construyen wheel y export
dos veces, rechazan symlinks, comparan digests e instalan el entrypoint en un
target limpio. Estos artefactos no equivalen a firma, registry publicado ni
nivel SLSA.

Una migración declara versión origen/destino, schemas afectados, pasos, reversa
y receipt. La política ejecutable de compatibilidad y deprecación vive en
`../profiles/compatibility-policy.json` y debe ser consumible sin clonar la
implementación. Mientras no exista una versión
previa materializada bajo esa política, el soporte N/N-1 permanece contratado,
no demostrado.

La generación y verificación local de checksum, SBOM y provenance está en
`../../modules/supply-chain-core/src/edaios_supply_chain/artifacts.py`. Ese
módulo no firma, publica ni asigna identidad al artefacto.

`.specify/release.json` separa el baseline instalado de un candidato de
release. Sin manifest explícito, el gate declara `baseline-no-candidate` y no
permite inferir publicación. `tools/publishing/prepare_core_release.py` prepara
un snapshot determinista en el path gobernado de una feature; el commit
candidato fija sus bytes. El checker calcula el estado operativo sin
reescribirlo: un commit limpio
puede quedar `ready-for-approval`; EvidenceReceipt v2, PolicyProfile,
AuthorityRegistry, GitCutoverTarget canónico y ApprovalReceipt válidos producen
`locally-approved`; solo un GitCutoverReceipt coherente con branch, tag, checks,
protección, default branch, evidencia del proveedor y publicación durable de
attestations permite declarar `sealed-by-authorized-observation`. El checker
valida la observación aportada, no consulta al proveedor en vivo. El
procedimiento de promoción y reversa está en `docs/core-release-cutover.md`.

El resultado cumple `edaios.core-release-verification-report/v1` y separa
cuatro ejes: `candidate_status`, `readiness`, `status` y `verification_mode`.
`status: valid` significa que un candidato explícito, sus inputs y artefactos coinciden bajo
validación local; no es aprobación. `provider_live_verified` permanece siempre
`false` porque este Core valida evidencia suministrada, no integra un proveedor.
