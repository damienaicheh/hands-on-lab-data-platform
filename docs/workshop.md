🎯 Vision globale du workshop

👉 Objectif :


🧩 Lab 0 — Introduction & Architecture
🎓 Objectif

Comprendre l’architecture globale.

Foundry IQ vs Fabric IQ (rôle de chacun)
Agents + Knowledge + Retrieval
Real-time vs batch

Architecture cible :

Agent orchestrator => Agent Fabric => Vente
                   => Agent Foundry => Ventes de nouveaux / produits / promotions


🧱 Lab 1 — Setup des données multi-domaines (Prerequis)
🎓 Objectif

=> Scripts Terraform (Fabric Capacity, Foundry)
=> ms-fabric-cli
=> Scripts Notebooks dans Fabric au démarrage + base RTI
4 domaines distincts (ex : Finance, RH, Sales, Supply)


📚 Lab 2 — Knowledge Base & Knowledge Sources
🎓 Objectif

Storage Account => Promos
Source vers interne

Knowledge Source

🔍 Lab 3 — Retrieval avancé (Blob + AI Search)
🎓 Objectif
Mettre en place une stratégie de recherche performante.
Contenu

Connecter Blob Storage
Configurer AI Search
Implémenter :

Retrieval depuis Blob via AI Search
Hybrid search (keyword + semantic)

🏢 Lab 4 — Foundry IQ Managed
🎓 Objectif
Industrialiser.
Contenu

Déploiement Managed
Gouvernance :

monitoring
coûts
scaling

🤖 Lab 5 — Agent Retrieval & grounding
🎓 Objectif
Créer des agents capables d'exploiter la donnée.
Contenu

Création d’un agent Foundry
Brancher :

Knowledge Base
AI Search


Implémenter :
grounding dynamique



👉 Notions :

Agent reasoning vs retrieval
Hallucination control


🔐 Lab 5 — Sécurité & Identity-based access ?
🎓 Objectif
Faire un agent context-aware selon l’utilisateur.
Contenu

Implémenter filtrage :

par utilisateur
par groupe


Simulation :

user A voit Finance
user B voit RH


# Foundry IQ vs Fabric IQ vs Foundry RTI

🔗 Lab 6 — Intégration Fabric & Ontology
🎓 Objectif
Structurer les données intelligemment.
Contenu

Connecter Fabric IQ
Introduire une Ontology / Semantic layer
Mapper :

données entre domaines

Lab 6 - Sécurité & Identity-based access pour Fabric


👉 Notions :

Data modeling pour agents
Alignement sémantique


⚡ Lab 7 — Real-time (Fabric RTI)
🎓 Objectif
Introduire le temps réel.
Contenu

Ingestion temps réel (Fabric RTI)
Connecter avec Foundry IQ
Agent capable de :

répondre avec données temps réel

=> Scripts de maj des données Fabric RTI => Nouvelle 

👉 Notions :

Streaming vs batch
Freshness des données


🔄 Lab 8 — MCP & interop agents
🎓 Objectif
Brancher plusieurs systèmes ensemble.
Contenu

Introduire MCP (Model Context Protocol)
Connecter :
MCP Dev (Optionnel)
MCP Fabric => Consommer BDD / RTI / Données
MCP Agentic 

🧠 Lab 9 — Agents spécialisés & orchestration
🎓 Objectif
Construire un système multi-agent.
Contenu

1 orchestrator
1 agent Fabric
1 agent Foundry
Routing intelligent