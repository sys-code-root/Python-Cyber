## SecToolkit: Dual-Layer Security Engine

Um toolkit de segurança em Python para validação e proteção de dados em trânsito (In-Transit) e em repouso (At-Rest), integrado a auditoria automatizada via LLM.

## O Problema
Garantir a integridade e a confidencialidade de dados entre a transferência HTTP e o armazenamento em disco costuma exigir várias ferramentas desconectadas. O SecToolkit resolve isso centralizando a assinatura HMAC, validação de JWT, checagem de cabeçalhos de segurança (HSTS, CSP, X-Frame-Options), criptografia simétrica (Fernet/AES) e relatórios automatizados de conformidade em uma única pipeline.

## Requisitos
Python 3.10+

## Dependências Python: 

cryptography, pyjwt, pydantic, requests, rich

(Opcional) Ollama rodando localmente com o modelo llama3 (para auditoria por IA)

## Bash
pip install cryptography pyjwt pydantic requests rich
Defina as variáveis de ambiente e execute:

## Bash
export JWT_SECRET="sua-chave-jwt-com-no-minimo-32-caracteres"
export HMAC_SECRET="sua-chave-hmac-com-no-minimo-32-caracteres"
python main.pyS