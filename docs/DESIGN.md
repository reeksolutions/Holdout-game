# HOLDOUT — Design doc

> Copied from the project README (owners: reek (Marquise) and his cousin). If something here conflicts with older notes, this wins.
> The code-level guide for AI agents is `AGENTS.md` in the repo root.

## 1. What Holdout is
**One-liner:** A persistent, open-world survival game with an action-horror feel. One big world spans several real-world biomes overrun by the infected. You scavenge real-world gear, build a base anywhere, trade in a military-run safe city, and fight both the infected and other players.

**Elevator pitch:** Rust's base-building and raiding, DayZ's persistent survival, and parkour movement you'd expect from a modern action game, set in a world where a desert city, a forest, a frozen north, a modern metropolis and a stacked hillside favela all exist on one map. It all centers on a guarded safe zone with NPC traders and a curfew.

**Tone: action + horror.** Daytime is action (loot, explore, parkour, fight — you're capable). Night is horror (infected faster and more aggressive, visibility drops, getting home matters).

**Story:** a mystery for now. Don't commit to a cause of the outbreak in code or text. Egyptian-style weapons in the desert are a flavor hook for a later lore reveal.

**Feel goal:** a "utopia that fell" vibe. Real-world items, real places, believable architecture.

## 2. Platform plan
| Stage | Where | Why |
|---|---|---|
| Now: prototype | Browser (single HTML file + three.js, Xbox controller) | Design and test feel, mechanics, systems. |
| Final: release | Roblox | So everyone can play. Free to play, cosmetics-only. |

Treat the browser build as the design spec. When a system is "done", write its rules and numbers into §14 so the port is easy. Keep systems simple and data-driven (tables of numbers, clear state machines).

## 3. Team
- **reek:** co-owner, game director, main prompter. Plays on Xbox controller, Chromebook and iPhone 14.
- **Cousin:** co-owner, equal say. World and design ideas (multi-biome world, favela, safe zone, NPC economy). Playtests.
- **AI agents:** most of the coding.

Working rules: edit only what's needed; a few features at a time; after every change say what changed / what didn't come out right / where to test; revert exactly when asked; casual, short tone.

## 4. Design pillars
1. Movement feels like a real game — fluid parkour, no teleporting or snapping.
2. Combat is skill-based — readable telegraphs, dodge, block, parry, combos.
3. Fair, never pay-to-win — power from gear you find/craft and base upgrades; money buys cosmetics only.
4. One big, varied world built from believable real-world places.
5. Persistence — base, stash and world survive between sessions.
6. Controller-first.
7. Detailed visuals — rigged, animated characters.

## 5. The world
One big open map, no loading between zones. Persistent survival (not extraction runs).

| Biome | Look and feel |
|---|---|
| Desert city | Middle Eastern style: flat-roof sandstone, markets, alleys, rooftops, domes, dust, palms. Egyptian bronze weapons. (Prototype style today.) |
| Forest | Dense trees, cabins, rivers, ranger stations |
| Cold / snow | Mountains, frozen towns, blizzards (warmth mechanic later) |
| Modern city | Skyscrapers, highways, malls, parking structures |
| Favela / hillside | Stacked homes on a hillside, stairs everywhere, tangled power lines. Signature biome. |

**Safe zone:** guarded zone inside the main city, military enforcement, NPC traders (buy/sell/trade), curfew at night, no PvP inside. You can build your base anywhere.

### 5.4 Riverdale (current playable map, B141 blockout, B142 art pass)
A ~500 m abandoned American town being swallowed by the woods, dusk-blue and wet: highway entrance with a "RIVERDALE NEXT RIGHT" sign and a quarantine checkpoint (spawn),
BRADLEY'S gas station (red-stripe canopy, pumps, GAS/FOOD/COLD BEER/LOTTO pole sign, AUTO SERVICE garage, ICE box), PINE VIEW two-storey motel (upstairs walkway + stairs, neon sign, drained pool),
brick Main Street with upper floors, blade signs, painted HARDWARE wall sign and the "OUR TOWN · OUR HOME · STILL HERE" banner, water tower, craftsman porch houses (siding, mailboxes, bins, chimneys, ivy) + church,
RIVERDALE MEDICAL CENTER (portico, red-cross sign, EMERGENCY neon, ambulance, stretcher, wheelchair, cones), industrial yard (metal warehouse, smokestack, depot, substation, junkyard, containers, radio tower),
river + rusted truss bridge to the east. Wet asphalt with puddles. Boundaries: collapsed bridge (S), rockslide (N), closed bridge (E), deep woods (W) — future expansion routes.
Art kit (`dressB`, `dressBox`, `upper`, `blade`, `neonSign`, `ivyOn`, `lampSpot` light pool of 6 real lights) lives just above `buildForest()`.

## 6. Core loop
Gear up → head out → fight or avoid → get back alive → upgrade gear and base → push into harder zones, raid or defend.

## 7. Player and progression
Custom character. No XP or levels — power comes from better gear (looted/crafted) and base upgrades. Skill matters most.
**Death:** keep equipped gear, lose backpack contents (dropped at death spot, marked on map). Prototype currently drops everything.

## 8. PvP, PvE, raiding
PvP + PvE everywhere outside the safe zone; Rust-style raiding; 1v1 duels (format TBD). Before real multiplayer: AI bandit bases and AI raiders.

## 9. Monetization (Roblox)
Cosmetics only. Never pay-to-win.

## 10. The infected
Implemented now (not locked): **Stalker** (standard, grabs), **Spitter** (ranged acid), **Crawler** (fast flanker, pounce), **Juggernaut** (armored tank), **Hound** (pack). Plus "The Twisted" runner on test/forest maps.
Rules every infected follows: every melee attack is telegraphed (0.45–0.75 s windup, arms up, orange glow, sound) and only lands if you're still in range and in front; a whiff opens a ~0.6 s punish window where your next hit is a COUNTER (1.5x).

## 11–13. Prototype
See `AGENTS.md` for files, code map and tests. Test map spawn is (0, 0, 7): vault lane x≈-18, climb lane x≈-9, ledge lane x≈0, platform lane x≈12, west lane x≈-26, house x≈22, shooting range x≈-25 z≈28.

## 12. Controls (controller)
| Input | Action |
|---|---|
| Left stick | Move (full push auto-sprint, L3 sprint) |
| Right stick | Look / aim |
| A | Jump, vault, climb (context); place when building |
| B | Tap: crouch. Double-tap: dodge roll |
| X | Use / gather / search / pick up |
| Y | Swap weapon |
| RT | Attack combo / hold heavy / fire |
| LT | Aim (guns) / block, tap to parry (melee) |
| LB | Flashlight |
| RB | Quick heal; rotate when building |
| D-pad | Map / Build / Eat / Craft |
| View | Backpack |

## 14. Mechanics spec (numbers to port)
### Movement (current build)
- Momentum movement: run 3.95 m/s, sprint 6.4 (×1.15 from the pack bonus), acceleration 6, deceleration 8, air control 2.5, turn 10, gravity 25, jump velocity 7.7.
- Crouch 1.5, aiming 1.8, blocking 1.6, charging a heavy 1.4. Backpack open ×0.42.
- Dodge roll: double-tap B within 0.26 s, i-frames, no roll in the air.
- Animation lock: landings and parkour finish before you can move again (`P.lockT`).

### Parkour (one button reads the world)
- Scan along movement up to 1.8 m (3.0 sprinting). Step height 0.45 m.
- Window: sill 0.45–1.45 m, lintel 0.8–2.3 m above — hop through, or dive + roll if the far side is >0.9 m lower.
- Vault: tallest part ≤1.5 m, depth ≤1.9 m → Kong vault (all vaults use it now).
- Climb: up to 2.75 m. Climb over: thin wall (<1.3 m deep) taller than 1.5 m — no roll after.
- Ledge grab: top 2.75–3.45 m, within 1 m; mid-air grab if edge is 0.3–2.35 m above feet.
- Never teleport; speed carries through vaults (85–92%); can't re-grab the same edge for 1 s.

### Combat
- Light combo A→B→C: ~0.5/0.56/0.82 s, damage ×1/×1.15/×1.75, chain window swing+0.32 s, steps toward targets within 3.6 m.
- Heavy (hold ≥0.32 s, charge 0.8 s): damage ×(1.6+1.2·charge).
- Block: 25% damage (50% vs Juggernaut). Parry: block within 0.28 s of the strike → 0 damage, enemy stunned 1.3 s.
- Counter after a whiff ×1.5. No stunlocking with light hits. Hit-stop 0.055/0.1/0.14/0.12 s.
- Guns: shots go down the crosshair (camera ray) then spread; barrel is corrected onto the crosshair in ADS and hip fire.

## 15. Roadmap (next, roughly in order)
Stamina · combat polish (hit reacts, infected look, "drop some" death) · loot loop · safe zone prototype · parkour in the real city · new biomes (favela first) · AI bandits and raids · infected roster redesign · real multiplayer → Roblox port.
Animation work in progress: movement, parkour, pistol, rifle done → melee, getting hurt, survival next.

## 16. Open questions
PvP/duel format · curfew details · infected roster · lore · character creation depth · vehicles · matchmaking · final name.

## Visual style (apply to all design work)
Dystopian low-poly horror: simple shapes, flat colors, dark tense mood. Muted dusty palette (sand, tan, cream, sandstone, ash gray) with sparing accents (rust red, faded blue, bronze, sickly green). Harsh washed-out days, very dark cold-blue nights, fog and dust limit view distance. Horror from atmosphere, not gore. Survivors in mismatched scavenged gear with oversized key pieces. Everything dusty, worn and repaired.
