# Undo, redeploy, and what changed

Everything below refers to the project folder
`C:\Users\Abin ag\Downloads\Sales-Operations-Intelligence-Copilot`.

## Local preview

Serve the static site locally:

```powershell
python -m http.server 8080 --directory web
# http://127.0.0.1:8080
```

The `web/` folder is a self-contained static site. The Python services
(and Ollama) stay local.
