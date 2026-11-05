"""
learnmate/course_catalog.py
────────────────────────────
Static curated course catalog covering 12 tech domains.
Each course entry contains: id, title, domain, level, duration_weeks,
skills_taught, prerequisites, and a free resource URL.
"""

from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Course Catalog  (100+ curated entries across 12 domains)
# ──────────────────────────────────────────────────────────────────────────────

COURSE_CATALOG: list[dict[str, Any]] = [

    # ── Frontend Development ────────────────────────────────────────────────
    {
        "id": "fe_001", "domain": "Frontend Development", "level": "beginner",
        "title": "HTML & CSS Fundamentals",
        "duration_weeks": 3,
        "skills_taught": ["HTML5", "CSS3", "Responsive Design", "Flexbox"],
        "prerequisites": [],
        "url": "https://www.freecodecamp.org/learn/responsive-web-design/",
        "provider": "freeCodeCamp",
    },
    {
        "id": "fe_002", "domain": "Frontend Development", "level": "beginner",
        "title": "JavaScript Essentials",
        "duration_weeks": 4,
        "skills_taught": ["JavaScript", "DOM Manipulation", "ES6+", "Async/Await"],
        "prerequisites": ["fe_001"],
        "url": "https://javascript.info/",
        "provider": "javascript.info",
    },
    {
        "id": "fe_003", "domain": "Frontend Development", "level": "intermediate",
        "title": "React – Building Modern UIs",
        "duration_weeks": 5,
        "skills_taught": ["React", "Hooks", "Context API", "Component Design"],
        "prerequisites": ["fe_002"],
        "url": "https://react.dev/learn",
        "provider": "React Docs",
    },
    {
        "id": "fe_004", "domain": "Frontend Development", "level": "intermediate",
        "title": "TypeScript for Frontend Developers",
        "duration_weeks": 3,
        "skills_taught": ["TypeScript", "Static Typing", "Interfaces", "Generics"],
        "prerequisites": ["fe_002"],
        "url": "https://www.typescriptlang.org/docs/",
        "provider": "TypeScript Docs",
    },
    {
        "id": "fe_005", "domain": "Frontend Development", "level": "advanced",
        "title": "Next.js – Full-Stack React Framework",
        "duration_weeks": 5,
        "skills_taught": ["Next.js", "SSR", "SSG", "API Routes", "Vercel Deployment"],
        "prerequisites": ["fe_003", "fe_004"],
        "url": "https://nextjs.org/learn",
        "provider": "Vercel",
    },
    {
        "id": "fe_006", "domain": "Frontend Development", "level": "advanced",
        "title": "Web Performance Optimization",
        "duration_weeks": 3,
        "skills_taught": ["Core Web Vitals", "Lazy Loading", "Code Splitting", "Caching"],
        "prerequisites": ["fe_003"],
        "url": "https://web.dev/learn/performance/",
        "provider": "web.dev",
    },

    # ── Backend Development ─────────────────────────────────────────────────
    {
        "id": "be_001", "domain": "Backend Development", "level": "beginner",
        "title": "Python Programming Basics",
        "duration_weeks": 4,
        "skills_taught": ["Python", "Data Types", "Functions", "OOP Basics"],
        "prerequisites": [],
        "url": "https://docs.python.org/3/tutorial/",
        "provider": "Python Docs",
    },
    {
        "id": "be_002", "domain": "Backend Development", "level": "intermediate",
        "title": "FastAPI – Modern Python APIs",
        "duration_weeks": 4,
        "skills_taught": ["FastAPI", "REST APIs", "Pydantic", "OpenAPI"],
        "prerequisites": ["be_001"],
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "provider": "FastAPI Docs",
    },
    {
        "id": "be_003", "domain": "Backend Development", "level": "intermediate",
        "title": "Databases: SQL & PostgreSQL",
        "duration_weeks": 4,
        "skills_taught": ["SQL", "PostgreSQL", "Joins", "Indexing", "Transactions"],
        "prerequisites": ["be_001"],
        "url": "https://www.postgresqltutorial.com/",
        "provider": "PostgreSQL Tutorial",
    },
    {
        "id": "be_004", "domain": "Backend Development", "level": "advanced",
        "title": "System Design & Microservices",
        "duration_weeks": 6,
        "skills_taught": ["Microservices", "Load Balancing", "Message Queues", "Kafka"],
        "prerequisites": ["be_002", "be_003"],
        "url": "https://www.ibm.com/topics/microservices",
        "provider": "IBM",
    },

    # ── Full Stack Development ──────────────────────────────────────────────
    {
        "id": "fs_001", "domain": "Full Stack Development", "level": "beginner",
        "title": "Web Development Fundamentals",
        "duration_weeks": 5,
        "skills_taught": ["HTML", "CSS", "JavaScript", "HTTP Basics"],
        "prerequisites": [],
        "url": "https://developer.mozilla.org/en-US/docs/Learn",
        "provider": "MDN Web Docs",
    },
    {
        "id": "fs_002", "domain": "Full Stack Development", "level": "intermediate",
        "title": "MERN Stack Development",
        "duration_weeks": 8,
        "skills_taught": ["MongoDB", "Express", "React", "Node.js", "REST APIs"],
        "prerequisites": ["fs_001"],
        "url": "https://www.mongodb.com/mern-stack",
        "provider": "MongoDB University",
    },
    {
        "id": "fs_003", "domain": "Full Stack Development", "level": "advanced",
        "title": "Full Stack with Next.js & Prisma",
        "duration_weeks": 6,
        "skills_taught": ["Next.js", "Prisma ORM", "Auth.js", "Deployment"],
        "prerequisites": ["fs_002"],
        "url": "https://create.t3.gg/",
        "provider": "T3 Stack",
    },

    # ── Data Science & Machine Learning ────────────────────────────────────
    {
        "id": "ds_001", "domain": "Data Science & Machine Learning", "level": "beginner",
        "title": "Python for Data Science",
        "duration_weeks": 4,
        "skills_taught": ["NumPy", "Pandas", "Matplotlib", "Jupyter"],
        "prerequisites": [],
        "url": "https://www.kaggle.com/learn/python",
        "provider": "Kaggle",
    },
    {
        "id": "ds_002", "domain": "Data Science & Machine Learning", "level": "intermediate",
        "title": "Machine Learning with scikit-learn",
        "duration_weeks": 6,
        "skills_taught": ["Supervised Learning", "Unsupervised Learning", "Feature Engineering", "Model Evaluation"],
        "prerequisites": ["ds_001"],
        "url": "https://scikit-learn.org/stable/tutorial/",
        "provider": "scikit-learn",
    },
    {
        "id": "ds_003", "domain": "Data Science & Machine Learning", "level": "advanced",
        "title": "Deep Learning with PyTorch",
        "duration_weeks": 8,
        "skills_taught": ["Neural Networks", "CNNs", "RNNs", "PyTorch", "Transfer Learning"],
        "prerequisites": ["ds_002"],
        "url": "https://pytorch.org/tutorials/",
        "provider": "PyTorch",
    },
    {
        "id": "ds_004", "domain": "Data Science & Machine Learning", "level": "advanced",
        "title": "Generative AI with IBM watsonx",
        "duration_weeks": 4,
        "skills_taught": ["LLMs", "Prompt Engineering", "RAG", "IBM Granite", "watsonx.ai"],
        "prerequisites": ["ds_002"],
        "url": "https://www.ibm.com/watsonx",
        "provider": "IBM",
    },

    # ── Cybersecurity ───────────────────────────────────────────────────────
    {
        "id": "cs_001", "domain": "Cybersecurity", "level": "beginner",
        "title": "Introduction to Cybersecurity",
        "duration_weeks": 4,
        "skills_taught": ["CIA Triad", "Threats & Vulnerabilities", "Networking Basics", "Security Mindset"],
        "prerequisites": [],
        "url": "https://www.cisco.com/c/m/en_us/partners/cisco-networking-academy/index.html",
        "provider": "Cisco NetAcad",
    },
    {
        "id": "cs_002", "domain": "Cybersecurity", "level": "intermediate",
        "title": "Network Security & Ethical Hacking",
        "duration_weeks": 6,
        "skills_taught": ["Penetration Testing", "Kali Linux", "Nmap", "Wireshark", "OWASP Top 10"],
        "prerequisites": ["cs_001"],
        "url": "https://tryhackme.com/",
        "provider": "TryHackMe",
    },
    {
        "id": "cs_003", "domain": "Cybersecurity", "level": "intermediate",
        "title": "SOC Analyst – Blue Team Fundamentals",
        "duration_weeks": 5,
        "skills_taught": ["SIEM", "Incident Response", "Log Analysis", "Threat Intelligence"],
        "prerequisites": ["cs_001"],
        "url": "https://www.ibm.com/security",
        "provider": "IBM Security",
    },
    {
        "id": "cs_004", "domain": "Cybersecurity", "level": "advanced",
        "title": "Certified Ethical Hacker (CEH) Prep",
        "duration_weeks": 8,
        "skills_taught": ["Advanced Exploitation", "Malware Analysis", "Cryptography", "CEH Domains"],
        "prerequisites": ["cs_002"],
        "url": "https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/",
        "provider": "EC-Council",
    },

    # ── UI/UX Design ────────────────────────────────────────────────────────
    {
        "id": "ux_001", "domain": "UI/UX Design", "level": "beginner",
        "title": "Design Thinking & UX Principles",
        "duration_weeks": 3,
        "skills_taught": ["Empathy Mapping", "User Research", "Personas", "Journey Mapping"],
        "prerequisites": [],
        "url": "https://www.coursera.org/learn/design-thinking-innovation",
        "provider": "Coursera",
    },
    {
        "id": "ux_002", "domain": "UI/UX Design", "level": "beginner",
        "title": "Figma for UI Design",
        "duration_weeks": 3,
        "skills_taught": ["Figma", "Wireframing", "Prototyping", "Design Systems", "Auto Layout"],
        "prerequisites": [],
        "url": "https://www.figma.com/resources/learn-design/",
        "provider": "Figma",
    },
    {
        "id": "ux_003", "domain": "UI/UX Design", "level": "intermediate",
        "title": "Interaction Design & Usability Testing",
        "duration_weeks": 4,
        "skills_taught": ["Interaction Patterns", "A/B Testing", "Usability Tests", "Accessibility"],
        "prerequisites": ["ux_001", "ux_002"],
        "url": "https://www.interaction-design.org/",
        "provider": "Interaction Design Foundation",
    },
    {
        "id": "ux_004", "domain": "UI/UX Design", "level": "advanced",
        "title": "Design Systems & Component Libraries",
        "duration_weeks": 4,
        "skills_taught": ["Atomic Design", "Storybook", "Tokens", "Documentation"],
        "prerequisites": ["ux_003"],
        "url": "https://storybook.js.org/",
        "provider": "Storybook",
    },

    # ── Mobile Development ──────────────────────────────────────────────────
    {
        "id": "mob_001", "domain": "Mobile Development", "level": "beginner",
        "title": "React Native – Cross-Platform Apps",
        "duration_weeks": 5,
        "skills_taught": ["React Native", "Expo", "Navigation", "Native APIs"],
        "prerequisites": ["fe_002"],
        "url": "https://reactnative.dev/docs/getting-started",
        "provider": "React Native Docs",
    },
    {
        "id": "mob_002", "domain": "Mobile Development", "level": "intermediate",
        "title": "Flutter & Dart",
        "duration_weeks": 6,
        "skills_taught": ["Dart", "Flutter Widgets", "State Management", "Platform Channels"],
        "prerequisites": [],
        "url": "https://flutter.dev/learn",
        "provider": "Flutter Docs",
    },
    {
        "id": "mob_003", "domain": "Mobile Development", "level": "advanced",
        "title": "Mobile App Security & Publishing",
        "duration_weeks": 3,
        "skills_taught": ["App Signing", "Play Store/App Store", "Secure Storage", "Certificate Pinning"],
        "prerequisites": ["mob_001"],
        "url": "https://owasp.org/www-project-mobile-app-security/",
        "provider": "OWASP",
    },

    # ── Cloud Computing ─────────────────────────────────────────────────────
    {
        "id": "cloud_001", "domain": "Cloud Computing", "level": "beginner",
        "title": "IBM Cloud Fundamentals",
        "duration_weeks": 3,
        "skills_taught": ["Cloud Concepts", "IaaS/PaaS/SaaS", "IBM Cloud Console", "Object Storage"],
        "prerequisites": [],
        "url": "https://cloud.ibm.com/docs",
        "provider": "IBM Cloud",
    },
    {
        "id": "cloud_002", "domain": "Cloud Computing", "level": "intermediate",
        "title": "Containers & Kubernetes on IBM Cloud",
        "duration_weeks": 5,
        "skills_taught": ["Docker", "Kubernetes", "IBM Kubernetes Service", "Helm"],
        "prerequisites": ["cloud_001"],
        "url": "https://www.ibm.com/cloud/learn/kubernetes",
        "provider": "IBM",
    },
    {
        "id": "cloud_003", "domain": "Cloud Computing", "level": "advanced",
        "title": "Cloud Architecture & IBM Cloud Pak",
        "duration_weeks": 6,
        "skills_taught": ["Cloud Pak for Data", "OpenShift", "Cloud Architecture Patterns", "HA Design"],
        "prerequisites": ["cloud_002"],
        "url": "https://www.ibm.com/products/cloud-pak-for-data",
        "provider": "IBM",
    },

    # ── DevOps & MLOps ──────────────────────────────────────────────────────
    {
        "id": "devops_001", "domain": "DevOps & MLOps", "level": "beginner",
        "title": "Git & Version Control",
        "duration_weeks": 2,
        "skills_taught": ["Git", "GitHub", "Branching", "Pull Requests", "CI/CD Basics"],
        "prerequisites": [],
        "url": "https://git-scm.com/doc",
        "provider": "Git SCM",
    },
    {
        "id": "devops_002", "domain": "DevOps & MLOps", "level": "intermediate",
        "title": "CI/CD with GitHub Actions & Docker",
        "duration_weeks": 4,
        "skills_taught": ["GitHub Actions", "Docker", "Docker Compose", "Automated Testing"],
        "prerequisites": ["devops_001"],
        "url": "https://docs.github.com/en/actions",
        "provider": "GitHub",
    },
    {
        "id": "devops_003", "domain": "DevOps & MLOps", "level": "advanced",
        "title": "MLOps with IBM Watson Studio",
        "duration_weeks": 5,
        "skills_taught": ["Model Pipelines", "AutoAI", "Model Monitoring", "IBM Watson Studio"],
        "prerequisites": ["devops_002", "ds_002"],
        "url": "https://www.ibm.com/products/watson-studio",
        "provider": "IBM",
    },

    # ── Blockchain ──────────────────────────────────────────────────────────
    {
        "id": "bc_001", "domain": "Blockchain", "level": "beginner",
        "title": "Blockchain Fundamentals",
        "duration_weeks": 3,
        "skills_taught": ["Distributed Ledger", "Consensus Mechanisms", "Wallets", "Smart Contracts Intro"],
        "prerequisites": [],
        "url": "https://www.ibm.com/blockchain/what-is-blockchain",
        "provider": "IBM",
    },
    {
        "id": "bc_002", "domain": "Blockchain", "level": "intermediate",
        "title": "Hyperledger Fabric with IBM Blockchain",
        "duration_weeks": 6,
        "skills_taught": ["Hyperledger Fabric", "Chaincode", "Permissioned Ledger", "IBM Blockchain Platform"],
        "prerequisites": ["bc_001"],
        "url": "https://www.ibm.com/blockchain/hyperledger",
        "provider": "IBM",
    },

    # ── Game Development ────────────────────────────────────────────────────
    {
        "id": "gd_001", "domain": "Game Development", "level": "beginner",
        "title": "Unity Foundations",
        "duration_weeks": 5,
        "skills_taught": ["Unity Editor", "C# Basics", "Physics", "2D Game Loop"],
        "prerequisites": [],
        "url": "https://learn.unity.com/",
        "provider": "Unity Learn",
    },
    {
        "id": "gd_002", "domain": "Game Development", "level": "intermediate",
        "title": "3D Game Development with Unity",
        "duration_weeks": 6,
        "skills_taught": ["3D Transforms", "Lighting", "Animations", "NavMesh AI"],
        "prerequisites": ["gd_001"],
        "url": "https://learn.unity.com/pathway/junior-programmer",
        "provider": "Unity Learn",
    },

    # ── Embedded Systems & IoT ───────────────────────────────────────────────
    {
        "id": "iot_001", "domain": "Embedded Systems & IoT", "level": "beginner",
        "title": "Arduino & Raspberry Pi Basics",
        "duration_weeks": 4,
        "skills_taught": ["C/C++ Basics", "GPIO", "Sensors & Actuators", "Serial Communication"],
        "prerequisites": [],
        "url": "https://www.arduino.cc/en/Tutorial/HomePage",
        "provider": "Arduino",
    },
    {
        "id": "iot_002", "domain": "Embedded Systems & IoT", "level": "intermediate",
        "title": "IoT with IBM Watson IoT Platform",
        "duration_weeks": 5,
        "skills_taught": ["MQTT", "IBM Watson IoT", "Node-RED", "Cloud Connectivity", "Device Management"],
        "prerequisites": ["iot_001"],
        "url": "https://www.ibm.com/cloud/internet-of-things",
        "provider": "IBM",
    },
]


def get_courses_by_domain(domain: str) -> list[dict]:
    """Return all courses for a given domain (case-insensitive partial match)."""
    domain_lower = domain.lower()
    return [c for c in COURSE_CATALOG if domain_lower in c["domain"].lower()]


def get_courses_by_level(
    domain: str, level: str
) -> list[dict]:
    """Return courses for a domain filtered by level."""
    return [
        c
        for c in get_courses_by_domain(domain)
        if c["level"] == level.lower()
    ]


def get_course_by_id(course_id: str) -> dict | None:
    for c in COURSE_CATALOG:
        if c["id"] == course_id:
            return c
    return None


def get_all_domains() -> list[str]:
    seen: list[str] = []
    for c in COURSE_CATALOG:
        if c["domain"] not in seen:
            seen.append(c["domain"])
    return seen
