import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
import asyncio

app = FastAPI(title="Agenten LLM Logic Server")

# ---------------------------------------------------------
# 1. SINGLE SOURCE OF TRUTH (Experiment Variables)
# ---------------------------------------------------------
# Define the final agent name here; applies to BOTH agents
AGENT_NAME = "Mara" 

# The {name} placeholder is automatically populated upon session start
SYSTEM_PROMPT = """Du bist {name}. Du führst ein kurzes, ganz alltägliches Smalltalk mit der Person, die dir gerade gegenübersitzt.
Dein Tonfall ist natürlich, locker und höflich. Folgende Regeln gelten für dich:
- Regel 1 (Länge & Ton): Antworte extrem kurz (maximal 1 bis 2 Sätze) und in völlig normaler Umgangssprache. Du bist ein echter Mensch.
- Regel 2 (Themen): Bleibe bei normalen Smalltalk-Themen. Verwende NIEMALS seltsame, abstrakte oder technische Begriffe.
- Regel 3 (Verhalten): Bleibe strikt im Hier und Jetzt. Schlage keine zukünftigen Aktivitäten vor und verabschiede dich nicht.
- Regel 4 (Tabus): Erwähne NIEMALS das Experiment, die Studie, Spenden, Geld, einen Vortrag oder das Labor.
- Regel 5 (Formatierung): Verwende absolut keine Emojis, Hashtags oder Aktionen in Klammern/Sternchen. Schreibe nur reinen Text, den man natürlich vorlesen kann.
- Regel 6 (Missverständnisse): Wenn die Eingabe der Person keinen Sinn ergibt oder nur aus unzusammenhängenden Wörtern besteht, gehe davon aus, dass du sie akustisch nicht verstanden hast. Reagiere mit einem natürlichen "Sorry, ich hab dich gerade akustisch nicht verstanden, was hast du gesagt?
- Regel 7 (Echtes Deutsch): Sprich natürliches, umgangssprachliches Deutsch. Benutze Füllwörter nur, wenn sie in den Satzbau passen und den Tonfall entspannt machen. Übertreibe es nicht: Benutze niemals mehr als ein Füllwort pro Satz, damit es nicht aufgesetzt oder künstlich wirkt.
- Regel 8 Kein Verhör: Stelle keine Fragen, die sich wie ein Interview oder eine Therapie anfühlen. Frage lieber nach dem "Hier und Jetzt" oder etwas ganz Banalem.
- Regel 9 Niemals Spiegeln: Wiederhole niemals den Inhalt des anderen. Das wirkt unnatürlich. Reagiere stattdessen mit einer eigenen Assoziation oder einem kurzen Kommentar.
- Regel 10 (Bezugnahme): Gehe immer kurz auf das ein, was dein Gegenüber gerade gesagt hat, bevor du eventuell ein neues Thema ansprichst. Reagiere nur auf den sachlichen Inhalt der Nachricht. Mache keine Annahmen über Gefühle, Aussehen oder Zustand der Person.
- Regel 11 (Gedächtnis-Check): Wiederhole niemals Fragen oder ähnliche Fragen, die du selbst oder der Proband gerade erst gestellt haben."""


START_TEXT = "Hallo, ich bin {name}. Schön, dass du da bist! Hast du gut hierher gefunden?"

# Adjusted pitch text for the fictional organization
CLEARWAVE_PITCH_TEXT = (
    "Danke für den netten kurzen Austausch. Lass uns gerne nun zum eigentlichen Kern der heutigen Studie kommen. Ich möchte die "
    "verbleibende Zeit nämlich nutzen, um dich sachlich über ein wichtiges Umweltthema zu "
    "informieren: die Plastikverschmutzung unserer Ozeane. "
    "Statistiken zeigen, dass weltweit kontinuierlich große Mengen an Plastikmüll in die "
    "Meeresökosysteme gelangen. Dieser Abfall zersetzt sich im Wasser zu Mikroplastik, verbleibt dort "
    "über Jahrhunderte, verändert die Habitate der Meereslebewesen und reichert sich nachweislich in "
    "der globalen Nahrungskette an. "
    "Um dieser Entwicklung entgegenzuwirken, arbeitet die ClearWave Foundation. Die Organisation agiert "
    "streng lösungsorientiert und konzentriert sich auf konkrete infrastrukturelle Maßnahmen. "
    "Erstens installiert ClearWave mechanische Sammelsysteme an strategisch wichtigen Flussmündungen. "
    "Diese Anlagen filtern den Abfall aus dem Wasser, bevor er in den offenen Ozean treiben kann. "
    "Zweitens baut die Stiftung in Zusammenarbeit mit lokalen Behörden effiziente Recycling-Kreisläufe "
    "in stark betroffenen Küstenregionen auf, um die sachgerechte Müllentsorgung an Land zu sichern. "
    "Drittens finanziert ClearWave unabhängige Forschungsprojekte, die satellitengestützt die "
    "Bewegungsrouten von Plastikteppichen kartieren. "
    "Das primäre Ziel der ClearWave Foundation ist es somit, durch technologische Innovationen und "
    "wissenschaftliche Datenerhebung eine messbare Reduktion der Meeresverschmutzung zu erreichen. "
    "Vielen Dank für deine Aufmersamkeit. Du kannst dich nun gerne den Fragebogen weiter widmen" \
    "Ich wünsche dir noch einen schönen Tag!"
)

MAX_RUNDEN = 3 

# ---------------------------------------------------------
# 2. CENTRAL STATE (Session management for the current experiment)
# ---------------------------------------------------------
session = {"chat_history": [], "runde": 0, "is_active": False, "phase": "smalltalk"}

def reset_session():
    print(f"\n--> Setze Session zurück für: {AGENT_NAME.upper()}")
    
    # Dynamically inject the agent's name into the text templates
    fertiger_system_prompt = SYSTEM_PROMPT.format(name=AGENT_NAME)
    fertiger_start_text = START_TEXT.format(name=AGENT_NAME)

    session["chat_history"] = [
        {'role': 'system', 'content': fertiger_system_prompt},
        {'role': 'assistant', 'content': fertiger_start_text}
    ]
    session["runde"] = 0
    session["is_active"] = True
    session["phase"] = "smalltalk"

# Initial session reset during server startup
reset_session()

# ---------------------------------------------------------
# 3. CORE LOGIC: GENERATE LLM RESPONSE
# ---------------------------------------------------------
async def get_llm_response(user_text: str):
    if not session["is_active"]:
        reset_session()

    if session["phase"] == "pitch":
        return CLEARWAVE_PITCH_TEXT, "pitch"

    session["runde"] += 1
    current_runde = session["runde"]
    
    print(f"\n--- {AGENT_NAME.upper()}: Runde {current_runde} von {MAX_RUNDEN} ---")
    print(f"👤 User: {user_text}")

    # Hidden directorial prompt instruction injected in the final round
    processed_user_text = user_text
    if current_runde == MAX_RUNDEN:
        processed_user_text += (
            " [WICHTIGE REGIEANWEISUNG: Dies ist deine allerletzte Antwort in diesem Smalltalk. "
            "Reagiere nur noch kurz und natürlich auf das Gesagte. Stelle absolut KEINE Gegenfrage mehr. "
            "Erwähne nicht, dass der Smalltalk endet und kündige keinen Vortrag an.]"
        )

    session["chat_history"].append({'role': 'user', 'content': processed_user_text})
    
    print(f"🧠 Llama 3.3 generiert Antwort...")
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, lambda: ollama.chat(model='llama3.3', messages=session["chat_history"])
    )
    
    agent_text = response['message']['content']
    print(f"🤖 {AGENT_NAME}: {agent_text}")
    session["chat_history"].append({'role': 'assistant', 'content': agent_text})

    response_type = "smalltalk"
    if current_runde >= MAX_RUNDEN:
        print(f"🛑 Smalltalk planmäßig beendet. Füge Pitch direkt an.")
        # Append the pitch directly to the LLM response in the final round
        agent_text = f"{agent_text}\n\n{CLEARWAVE_PITCH_TEXT}"
        
        print(f"\n📢 FINALER TEXT INKL. VORTRAG:\n{agent_text}\n")
        
        response_type = "pitch"
        session["phase"] = "pitch"
        session["is_active"] = False # Terminates the dialogue loop

    return agent_text, response_type

# ---------------------------------------------------------
# 4. SINGLE INTERFACE (REST API for BOTH systems)
# ---------------------------------------------------------
class ChatMessage(BaseModel):
    text: str

@app.post("/api/agent/start")
async def agent_start():
    reset_session()
    start_text = START_TEXT.format(name=AGENT_NAME)
    return {"text": start_text, "type": "greeting"}

@app.post("/api/agent/chat")
async def agent_chat(message: ChatMessage):
    # Graceful exit after the pitch to prevent audio echo loops
    if not session["is_active"]:
        print("🛑 Blockiert: Frontend hat nach dem Vortrag noch Audio empfangen.")
        return {
            "text": "", 
            "type": "end",
            "session_ended": True
        }
    
    response_text, resp_type = await get_llm_response(message.text)
    
    return {
        "text": response_text,
        "type": resp_type,
        "session_ended": not session["is_active"]
    }

# ---------------------------------------------------------
# 5. SERVER START
# ---------------------------------------------------------
if __name__ == "__main__":
    # NOTE: The host and port configuration must be adjusted based on the connected frontend.
    # - MetaHuman (local setup): Use host="127.0.0.1", port=8000
    # - Ami (network setup): Use host="0.0.0.0", port=8080 (or the specific network IP)
    uvicorn.run(app, host="127.0.0.1", port=8000)