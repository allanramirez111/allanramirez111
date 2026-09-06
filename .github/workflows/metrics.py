"""Reescribe el bloque METRICS del README con datos de la API de GitHub.

Ve repos privados porque usa los PAT del propio dueño, a diferencia de las
instancias públicas de github-readme-stats. Dos tokens, a propósito:

  GH_TOKEN        PAT clásico, scope `read:user` (+ read:org). Solo contribuciones.
                  No da acceso a código.
  GH_TOKEN_REPOS  Uno o varios PAT de SOLO LECTURA separados por coma. Dan
                  lenguajes y commits. Un PAT fine-grained tiene UN solo resource
                  owner, así que hacen falta tantos como owners quieras contar
                  (tu cuenta + cada org). Los resultados se fusionan por repo.
                  Opcional: sin él el bloque se degrada a contribuciones y días.
  METRICS_EMAILS  Opcional, separados por coma: los correos con que has firmado
                  commits. Va en secret y no en el fuente porque incluye correos
                  corporativos que no deben quedar en un repo público. Sin él se
                  filtra por cuenta vinculada, que NO ve los commits firmados con
                  correos no registrados en tu cuenta (aquí eran 420 de 5.000).

Un solo PAT clásico con scope `repo` haría lo mismo, pero da lectura Y ESCRITURA
sobre todos los repos privados de las orgs, y este secret vive en un repo público.

Sin dependencias: solo stdlib.  Autocomprobación:  python3 metrics.py --check
"""
import collections, datetime, json, os, re, sys, time, urllib.error, urllib.request

Q_YO = "{ viewer { id contributionsCollection { contributionCalendar {" \
       " totalContributions weeks { contributionDays { contributionCount } } } } } }"

# `viewer.repositories(ownerAffiliations: ORGANIZATION_MEMBER)` NO devuelve todos los
# repos de las orgs —se saltaba los más grandes— y en cambio mete repos ajenos donde
# solo eres colaborador. Por eso las orgs se consultan explícitamente.
Q_REPOS = """
query($autor: CommitAuthor!) {
  viewer {
    repositories(first: 100, isFork: false, ownerAffiliations: [OWNER]) { nodes { ...R } }
    organizations(first: 10) { nodes { repositories(first: 100, isFork: false) { nodes { ...R } } } }
  }
}
fragment R on Repository {
  nameWithOwner
  languages(first: 15, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
  defaultBranchRef { target { ... on Commit { mios: history(author: $autor) { totalCount } } } }
}
"""

# Los notebooks y el HTML generado guardan sus salidas embebidas en base64: inflan el
# conteo por bytes y miden imágenes, no código.
EXCLUIDOS = {"Jupyter Notebook", "HTML", "CSS", "SCSS", "Dockerfile", "Makefile", "TeX"}
TOP_N = 6
ANCHO = 28


def barra(frac):
    """Bloques parciales: 1/8 de carácter de resolución. Redondeando a bloque entero,
    un 0,05% y un 3% se dibujaban idénticos."""
    u = round(frac * ANCHO * 8)
    return ("█" * (u // 8) + " ▏▎▍▌▋▊▉"[u % 8]).rstrip()


def mis_commits(repo):
    return ((repo.get("defaultBranchRef") or {}).get("target") or {}).get("mios", {}).get("totalCount", 0)


def _post(query, variables, token, intentos=4):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    for i in range(intentos):
        ultimo = i == intentos - 1
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                cuerpo = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 401 or ultimo:          # token malo: reintentar no ayuda
                raise SystemExit(f"API de GitHub: HTTP {e.code}"
                                 + (" — token invalido, revocado o mal pegado" if e.code == 401 else ""))
            time.sleep(int(e.headers.get("Retry-After") or 5 * 2 ** i))
            continue
        except (urllib.error.URLError, TimeoutError):
            if ultimo:
                raise SystemExit("no se pudo contactar la API de GitHub")
            time.sleep(5 * 2 ** i)
            continue
        errores = cuerpo.get("errors")           # un token sin scope devuelve 200 con errors
        if errores:
            tipos = sorted({e.get("type", "UNKNOWN") for e in errores})
            if tipos == ["RATE_LIMITED"] and not ultimo:
                time.sleep(60)
                continue
            # Solo los tipos: los mensajes de GraphQL citan repos y orgs por nombre, y
            # los logs de Actions de un repo público son públicos.
            raise SystemExit(f"GraphQL: {tipos} — reproducir en local con el mismo PAT")
        return cuerpo["data"]["viewer"]
    raise SystemExit("agotados los reintentos")


def consultar():
    # .strip(): pegar un token en `gh secret set` deja un \n al final con facilidad,
    # y "bearer ghp_...\n" devuelve 401 sin decir por qué.
    yo = _post(Q_YO, {}, os.environ["GH_TOKEN"].strip())
    token_repos = (os.environ.get("GH_TOKEN_REPOS") or "").strip()
    if not token_repos:
        return yo, None
    correos = [c.strip() for c in os.environ.get("METRICS_EMAILS", "").split(",") if c.strip()]
    autor = {"emails": correos} if correos else {"id": yo["id"]}
    repos = {}
    for tk in [t.strip() for t in token_repos.split(",") if t.strip()]:
        v = _post(Q_REPOS, {"autor": autor}, tk)
        vistos = list(v["repositories"]["nodes"])
        for org in v["organizations"]["nodes"]:
            vistos += org["repositories"]["nodes"]
        # Un token que no ve ni un repo con commits tuyos suele ser un fine-grained
        # sin aprobar en su org: la API no falla, solo devuelve menos. Fallar aquí
        # es preferible a publicar barras calculadas sobre la mitad del código.
        if not any(mis_commits(r) for r in vistos):
            raise SystemExit("un token de GH_TOKEN_REPOS no ve ningún repo con commits tuyos; "
                             "revisa que esté aprobado para su organización")
        repos.update({r["nameWithOwner"]: r for r in vistos})
    # Solo donde realmente escribiste: un repo de la org que nunca tocaste no dice
    # nada de ti, y su código falsearía las barras de lenguajes.
    return yo, [r for r in repos.values() if mis_commits(r)]


def render(yo, repos):
    cal = yo["contributionsCollection"]["contributionCalendar"]
    activos = sum(1 for w in cal["weeks"] for d in w["contributionDays"] if d["contributionCount"])
    linea = [f"**{cal['totalContributions']:,}** contributions in the last year",
             f"**{activos}** active days"]
    cuerpo = ""

    if repos:
        commits = sum(mis_commits(r) for r in repos)
        linea.append(f"**{commits:,}** commits authored across **{len(repos)}** repositories")
        por_lenguaje = collections.Counter()
        for repo in repos:
            for e in repo["languages"]["edges"]:
                if e["node"]["name"] not in EXCLUIDOS:
                    por_lenguaje[e["node"]["name"]] += e["size"]
        total = sum(por_lenguaje.values()) or 1
        barras = "\n".join(
            f"{nombre:<14} {barra(n / total):<{ANCHO}} {100 * n / total:5.1f}%"
            for nombre, n in por_lenguaje.most_common(TOP_N)
        ) or "(todos los lenguajes quedaron excluidos)"
        cuerpo = f"\n```text\n{barras}\n```\n"

    nota = "Language split by source bytes; notebooks and generated HTML excluded. " if repos else ""
    return (f"### Activity\n\n{' &nbsp;·&nbsp; '.join(linea)}\n{cuerpo}\n"
            f"<sub>{nota}Most of the work lives in private product repositories; these numbers "
            f"come from the GitHub API, not from a hand-written list. "
            f"Updated {datetime.date.today().isoformat()}.</sub>")


def escribir(bloque, ruta="README.md"):
    readme = open(ruta, encoding="utf-8").read()
    # Reemplazo por función: el retorno se usa literal, así que un "\" en el contenido
    # generado no se interpreta como escape.
    nuevo, n = re.subn(r"(<!--METRICS:start-->).*?(<!--METRICS:end-->)",
                       lambda _: f"<!--METRICS:start-->\n{bloque}\n<!--METRICS:end-->",
                       readme, flags=re.S)
    if n != 1:                                   # marcadores borrados o duplicados
        raise SystemExit(f"esperaba 1 bloque METRICS, encontré {n}")
    open(ruta, "w", encoding="utf-8").write(nuevo)


def _check():
    assert barra(1.0) == "█" * ANCHO and barra(0.0) == ""
    assert barra(0.0005) != barra(0.03)          # el bug de redondear a bloque entero
    yo = {"contributionsCollection": {"contributionCalendar": {"totalContributions": 1,
          "weeks": [{"contributionDays": [{"contributionCount": 0}, {"contributionCount": 3}]}]}}}
    assert "**1** active days" in render(yo, None) and "```" not in render(yo, None)
    r = {"nameWithOwner": "a/b", "languages": {"edges": [{"size": 9, "node": {"name": "Jupyter Notebook"}}]},
         "defaultBranchRef": {"target": {"mios": {"totalCount": 7}}}}
    assert mis_commits(r) == 7 and mis_commits({"defaultBranchRef": None}) == 0
    assert render(yo, [r]).count("```") == 2     # todo excluido no rompe el fence
    assert "**7** commits authored across **1** repositories" in render(yo, [r])
    print("ok")


if __name__ == "__main__":
    _check() if "--check" in sys.argv else escribir(render(*consultar()))
