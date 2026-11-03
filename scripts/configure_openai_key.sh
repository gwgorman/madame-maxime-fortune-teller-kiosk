#!/bin/bash
set -euo pipefail

config_dir="${HOME}/.config/madame-maxime"
secret_file="${config_dir}/secrets.env"

printf 'OpenAI project API key (input hidden): '
IFS= read -r -s api_key
printf '\n'
if [[ -z "${api_key}" ]]; then
    printf 'No key entered; configuration unchanged.\n' >&2
    exit 2
fi

umask 077
mkdir -p "${config_dir}"
temporary="$(mktemp "${config_dir}/secrets.env.XXXXXX")"
trap 'rm -f "${temporary}"' EXIT
printf 'OPENAI_API_KEY=%s\n' "${api_key}" > "${temporary}"
chmod 600 "${temporary}"
mv -f "${temporary}" "${secret_file}"
trap - EXIT
unset api_key
printf 'Saved private STT configuration to %s (mode 0600).\n' "${secret_file}"
