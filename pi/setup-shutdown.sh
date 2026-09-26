#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run using sudo.'; exit 1; }
test -x /usr/sbin/shutdown
test -x /usr/sbin/visudo
helper=$(mktemp)
rule=$(mktemp)
trap 'rm -f "$helper" "$rule"' EXIT
cat > "$helper" <<'EOF'
#!/bin/sh
[ "$#" = 0 ] || exit 1
exec /usr/sbin/shutdown -h now
EOF
printf '%s\n' 'markt1600 ALL=(root) NOPASSWD: /usr/local/sbin/winecellar-shutdown ""' > "$rule"
/usr/sbin/visudo -cf "$rule"
install -o root -g root -m 755 "$helper" /usr/local/sbin/winecellar-shutdown
install -o root -g root -m 440 "$rule" /etc/sudoers.d/winecellar-shutdown
printf '%s\n' 'Shutdown button enabled. This setup does NOT shut down the Pi.'
