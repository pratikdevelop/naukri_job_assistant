import re

def norm(value):
    return re.sub(r"[^a-z0-9+#.]+", " ", (value or "").lower())

def score_job(job, cfg):
    title = norm(job.get("job_title"))
    body = norm(" ".join(str(job.get(k, "")) for k in ["job_title", "skills", "description", "company"]))
    s = cfg["scoring"]
    score = 0
    reasons = []

    title_rules = {
        "mern": ["mern"], "node": ["node js", "node.js", "node"],
        "react": ["react js", "react.js", "react"],
        "full_stack": ["full stack", "fullstack"],
        "backend": ["backend", "back end"], "javascript": ["javascript"],
        "ai": ["ai engineer", "generative ai", "llm", "artificial intelligence"],
        "python": ["python"], "angular": ["angular"]
    }

    for key, needles in title_rules.items():
        if any(n in title for n in needles):
            score += s["title"].get(key, 0)
            reasons.append(key)

    skill_rules = {
        "typescript":["typescript","type script"], "express":["express","express.js"],
        "mongodb":["mongodb","mongo db"], "postgresql":["postgresql","postgres"],
        "nextjs":["next.js","nextjs"], "aws":["aws"], "docker":["docker"],
        "kafka":["kafka"], "redis":["redis"], "django":["django"],
        "fastapi":["fastapi","fast api"]
    }

    for key, needles in skill_rules.items():
        if any(n in body for n in needles):
            score += s["skills"].get(key, 0)
            reasons.append(key)

    if "senior" in title:
        score += s["penalties"]["senior"]
    if "lead" in title:
        score += s["penalties"]["lead"]
    if "manager" in title:
        score += s["penalties"]["manager"]
    if "mern" in title or ("node" in title and "react" in body):
        score += 5
        reasons.append("core MERN fit")

    return max(0, min(100, score)), ", ".join(reasons[:10]) or "general match"
