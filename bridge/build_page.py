"""Embed a results JSON into the interactive page (docs/index.html), replacing the data block in place."""
import re, sys
res = open(sys.argv[1] if len(sys.argv) > 1 else "results/bridge_results.json").read().strip()
p = "docs/index.html"
html = re.sub(r"/\*__DATA__\*/.*?/\*__END__\*/", lambda m: "/*__DATA__*/" + res + "/*__END__*/", open(p).read(), flags=re.S)
open(p, "w").write(html)
print("docs/index.html updated")
