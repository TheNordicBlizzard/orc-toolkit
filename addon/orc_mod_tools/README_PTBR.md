# ORC Mod Tools 1.1.2 — Blender 5.0.1

Addon de importação FM6S nativo v17/v18 para RE: Operation Raccoon City.
Candidato para revisão; **não é exportador validado no jogo**. [English](README.md).

## Uso e instalação após revisão
Preferências > Add-ons > Install from Disk; selecionar o ZIP revisado e ativar
ORC Mod Tools. Sidebar (`N`), aba **ORC**. Indexar SSG/edgemodel, selecionar MODEL,
importar. As opções controlam skin/rig placeholder, UVs e materiais de verdade.
Parsers vêm em `vendor/`; a pasta externa não é necessária nem tem precedência.
O caminho legado fica nas Preferências por compatibilidade de configuração.
Diretório do jogo é opcional, consultado apenas para ler skeletons.
Esta entrega não instala nada, não recarrega sessão do usuário e não altera jogo.

## Correções comprovadas e limites
- Normals por canto são vetores; erros da API não são mais engolidos. Comparadas
  com chamada independente correta da API Blender; armazenamento comprimido
  das normals do Blender não equivale a floats nativos byte-idênticos.
- UV primária do stride 60: half floats no offset 28. UVs secundárias não importadas.
- Skeleton 20SE descompactado de `dlc/**/Characters/skel`: joints em 0x10;
  0x08 contém tamanho dos dados custom. Nomes, parents, posições/quaternions locais
  são decodificados; spans inválidos e ciclos de parents são rejeitados.
- **Rig continua placeholder não vinculado:** paleta da malha e matrizes rest/bind
  não comprovadas. Grupos numéricos preservam as quatro influências u8 nativas.
  Sem parenting e sem modifier Armature automático. Counts iguais não validam rig.
  Skeletons ambíguos avisam sem impedir importação da geometria.
- **Materiais são prévia diffuse básica:** referência nativa da malha resolve MATB
  e DDS do mesmo SSG. Semantic diffuse conhecido 3014450751 liga Base Color do
  Principled. DDS real é empacotado na imagem Blender. Não reproduz shaders Hexane,
  alpha, normal/specular/emission nem busca recursos soltos. Edgemodel avulso sem
  recursos recebe materiais básicos e avisos explícitos.
- **Exportar SSG / converter edgemodel BLOQUEADOS**: CANCELLED antes de escrever.
  Writer legado emite tabelas incompatíveis e skin 2u16+2half, não 4u8+4u8.
  Scanner heurístico não prova aceitação nativa. Validação da sidebar usa as tabelas
  do importador nativo, sem afirmar compatibilidade no jogo.

## FBX / BLEND não são exportação para o jogo
Usar Arquivo > Exportar > FBX do Blender; Salvar Como para `.blend`.
Ada/Tweed reais foram exportados e reabertos/reimportados em processos factory
separados; comparados posições, triângulos, UVs, slots e hashes dos pixels diffuse.
FBX Tweed passou; FBX Ada NÃO é topology-exact: o importador Blender removeu
12 faces duplicadas em três malhas (ver diagnóstico entregue).
BLEND passou em ambos e preserva grupos numéricos e imagens empacotadas. **FBX só de malhas não
fornece nem valida rig/skin nativo animável.** O importador FBX pode reconstruir
nodes Color/Alpha separados. Não preserva shader original nem comprova SSG no jogo.
O Asset Explorer/CLI standalone é outra aplicação: não foi alterado ou incluído.
Bugs legados do CLI (UV seam e validate) ficam para tarefa separada. Writers em
vendor são legado para compatibilidade, não uma via funcional de exportação nativa.

## Evidências
Blender 5.0.1 factory-startup, backups vanilla Tweed/Ada e elitehunter real.
Logs RED/GREEN, `execution.json`, referência independente de geometria/UV/skin e
arquivos round-trip ficam ao lado do ZIP em `orc-addon-fix`. Nada validado no jogo.
Fonte original e cópia instalada não foram alteradas; pai revisa antes de instalar.
Avisos críticos e títulos usam EN/PT-BR; alguns labels legados permanecem PT-BR
ou bilíngues. Não há tradução integral do locale Blender.
Créditos: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

