# ORC Mod Tools — fluxo Blender separado

[English](ADDON.md) · [Índice](INDEX.pt-BR.md)

Explorer GUI, `orc_asset_helper.py` legado, addon ORC Mod Tools e CLI experimental são componentes distintos. Worker Blender do Explorer **não exige este addon**. Instalado **1.1.1 não foi alterado**. ZIP isolado **1.1.2** é candidato, não instalado/publicado; aprovação de instalação/release cabe ao pai. As 10 entradas exatas auditadas estão em [addon/orc_mod_tools](../addon/orc_mod_tools/README_PTBR.md), com vendor e avisos originais; nenhum addon instalado foi sobrescrito.

## Testar sem substituir seu ambiente
1. Use perfil Blender separado/sessão factory e ZIP auditado do release final. v1.0 público ainda não contém esse addon novo. Preserve backup de addon/configuração; não substitua 1.1.1 implicitamente.
2. Preferences → Add-ons → Install from Disk (texto varia por versão), escolha ZIP, habilite ORC Mod Tools e abra sidebar da View 3D. QA usou Blender 5.0.1; não conclua compatibilidade universal.
3. **Arquivos:** configure jogo/trabalho/Blender, abra SSG completo e lista plana de entradas/prévias. **Importação:** escolha FM6S real; textura ausente/layout desconhecido são limites, não sucesso.
4. **Configuração:** caminhos/idioma; avisos críticos e títulos EN/PT-BR, mas nem todo rótulo legado traduzido.
5. **Exportação:** blend para preservação testada; FBX tem limitações abaixo. Exportação/conversão nativa do jogo são **CANCELLED antes de escrever**, por segurança.
6. **Validação:** sucesso vale somente para propriedade testada, não aceitação no jogo, rig deformável ou comando CLI diferente.

## Correções do 1.1.2 isolado
Parser/contagem skeleton, normais nativas/API Blender, UV stride60 e diffuse MATB conhecido local ao arquivo. Influências nativas four-u8 são armazenadas em grupos numéricos **SEM autobind**, parenting ou Armature automático. Ada 180/Tweed 125 joints lidos não provam rig: associação paleta/rest/bind/skin **NÃO VALIDADA**, placeholder explicitamente sem vínculo.

## Exatidão e problemas conhecidos
- Blend do addon preserva geometria/UV/material/textura/pesos numéricos e duplicatas Ada. **Não** confundir com blend Explorer: Explorer remove 12 polígonos Ada duplicados em todos os formatos escolhidos.
- Ada FBX reimportado perde 12 duplicatas (10 + 1 + 1 em três malhas). Posições/UV restantes não provam topologia exata.
- Tweed FBX passou geometria/UV/material/textura, mas `numeric_skin_preserved: false`.
- Diffuse básico: 12 malhas Tweed / 15 Ada texturizadas no relatório; sem shaders originais completos alpha/normal/specular/UV secundário.
- Relatório ZIP **10/10**; fonte **18/20** (problemas Ada FBX e original-six); 6 testes UI e draw real separado em factory. Não somar como aprovação geral de funções.
- ZIP SHA256: `7118df49a6726ba05386e0f0763a5292fbdb187e5996fe70698741c5bb408c17`.

## CLI experimental — aprovação GUI não inclui CLI
O novo [CLI projeto e complemento NativeBridge](../tools/native_bridge/README.pt-BR.md) é separado deste CLI legado: somente posições FM6S v18 validadas, template imutável, saída/diff novos. Não libera writer geral ORC Mod Tools bloqueado nem substituições arbitrárias.
CLI legado inalterado e fora do ZIP. Bugs: perde seams UV, validate falha por `command_args` ausente, writer usa tabela/skin incompatíveis (2u16+2half legado versus four-u8 nativo). Não sobrescreva jogo nem anuncie roundtrip in-game. Não há receita CLI nativa aprovada para publicação; preservar originais/backups, novos destinos e aguardar tarefa própria de correção/QA.

Docstrings do writer vendor mantêm alegações históricas de round-trip/contagem para preservar a fonte auditada exata; **não são evidência atual de segurança**. Operadores nativos bloqueados; writer legado não aprovado por esta entrega.

Fontes: `DELIVERY_RESULTS.json` local e [cobertura](COVERAGE.pt-BR.md), sanitizados. [Avisos](../THIRD_PARTY_NOTICES.md).
