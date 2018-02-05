body ()
{
    IFS= read -r header;
    printf '%s\n' "$header";
    "$@"
}

record ()
{
    local logf=/tmp/output.${1//[^[:alnum]]/_}.$(date '+%Y-%m-%d_%H-%M');
    "$@" | tee $logf;
    echo '
--
output saved in:
  '"$logf"
}
