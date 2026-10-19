# HOLDOUT — guide for AI coding agents (Claude, Codex, Jules, Copilot, ChatGPT, Gemini…)

Read this whole file before you touch anything. The design doc is `docs/DESIGN.md`.

## What this is
A browser prototype of **Holdout**, a survival / action-horror game (desert city, parkour, melee + guns, base building, infected).
Owners: **reek (Marquise)** and his cousin. reek doesn't code; he plays on an **Xbox controller** (Chromebook / iPhone) and tells you what to change.
The final game is planned for Roblox; this prototype is where feel and systems get designed and tested.

## Files
| File | What it is |
|---|---|
| `index.html` | **The whole game.** One file, ~5,400 lines of plain JS inside one IIFE. three.js **r128** + GLTFLoader from CDN. |
| `mx_anims.json` | Mixamo animations retargeted onto our skeleton (keys `mx_*`, `mxb_*`, `mxj_*`, `mxv_*`, `mxh_*`, `mxp_*` pistol, `mxr_*` rifle, `mxi_*` injured, `mxs_*` saved/unused). |
| `anims.json` | Older Quaternius animation clips (still used for some moves). |
| `player.json` + `player_*.jpg`, `ranger.json`, `umm_*.json`, `wrapped.*` | Character / outfit / monster models (glTF JSON). |
| `sounds.json` | All sound effects (base64). |
| `tests/run_tests.py` | **Automated test** — run it after every change. |
| `tools/retarget/` | Pipeline that turns Mixamo FBX files into `mx_anims.json` entries. |
| `CREDITS.txt` | Asset licenses. Keep it updated when you add assets. |

## Rules (from reek — follow them)
1. **Edit only the code that's needed.** No rewrites, no reformatting, no "cleanup", no splitting the file.
2. A few features at a time. Test, then continue.
3. After every change tell reek, in short casual words: **what changed, what might be off, where on the map to test it.**
4. Never break: movement, parkour, aiming, the Mixamo animation layers. Run the tests.
5. If reek says "change it back", revert exactly (git makes this easy — use `git revert`).
6. Keep the visual style: dystopian low-poly horror, dusty desert palette (see `docs/DESIGN.md`).

## How to test (required before every commit)
```bash
pip install playwright && playwright install chromium   # once (skip install if Chromium exists)
cd tests && npm install && cd ..                         # once: local three.js so tests work offline
python3 tests/run_tests.py
```
It syntax-checks the script, boots the game headless (Chromium + SwiftShader), and checks: character + animations load,
sprint speed, jump, dodge roll, **every gun's aim lands on the crosshair (ADS and hip fire)**, and zero JS errors.
Screenshots land in `tests/shots/` — look at them when you change anything visual.
If you change a function the test hooks into (`buildWeapon('club');setGameUI(false)…` line or the `let dt=` line in `loop`), update the `H` list in `tests/run_tests.py`.
Add a check to `run_tests.py` for any new system you build.

Quick syntax-only check: extract the biggest `<script>` and run `node --check` on it (the test does this first).

## Playing it
Must be served over http (opening the file directly blocks the model loads):
`python3 -m http.server 8000` then open `http://localhost:8000/`. Or use the GitHub Pages link in README.md.
The menu has a **MAP** switch: Test Area (movement/combat lab) or Town (Ashford).

## Map of the code (line numbers drift — search the name)
**Switches & tuning tables (change numbers here first):**
- `ENABLE_INFECTED`, `TEST_INFECTED` (~line 510) — spawning switches.
- `MOVE` — run 3.95, sprint 6.4, accel/decel, air control, gravity 25, jump 7.7 (momentum movement).
- `STRIDE` (leg cadence), `KONG` (kong vault blend/land), `HEAVY` (climb/vault weight), `LEDGE` (pull-up), `CLEAR` (melee weapon clearance).
- `GUNANIM` (pistol recoil/kick), `PAIM`, `AIMFIX` (barrel-to-crosshair correction), `RIFLE` (rifle layer: jump hold, recoil), `CAMGUN` (hip camera height/level with a gun out).
- `W={…}` (~line 2230) — **every weapon and item**: damage, range, cooldown, mag, reload, recoil, grip offsets (`hp`, `g2`).

**Systems:**
- Animation loading: `MXL` (fetches `mx_anims.json`), `mxClip()`, `mxSwap()` (replaces base locomotion), `MX_SWAP`.
- Animation layers: `mxBaseSetup()` (directional, crouch transitions, turns, jumps `SOLD.MXJ`, vaults `SOLD.MV`, climb `SOLD.CL`, ledge `SOLD.HG`), `mxPistolSetup()` + `MXP_DEF` (`SOLD.PS`), `mxRifleSetup()` + `MXR_DEF` (`SOLD.RF`), `mxInjuredSetup()` (`SOLD.INJ`, below 40 HP).
- Per-frame pose: `soldierPose(dt,o)` — layer weights, procedural lean/twist, gun placement, melee IK. After it: `pistolAimFix()` (barrel → crosshair, uses `AIMCAM` = saved gameplay camera) and `rifleHands()` (left hand IK onto the handguard).
- Guns: `fireRifle()` (shots go down the camera ray), `shotRay()` (hitboxes; range targets in `TGT`), `startReload()`, `xhPitch()`.
- Melee: `attack()`, `heavyAttack()`, `doHit()`, `dmgZombie()`, `meleePose()`, `gripHand()` (hand IK).
- Parkour: `profileAt()`, `probeCtx()`, `doContext()`, `startAct()`, `updateAct()`, `tryLedge()`, `doRoll()`. Animation lock: `P.lockT`.
- World: `buildTestMap()`, `testRange()` (shooting range at x≈-25, z≈28), forest builder, `addSolid` box physics, `groundAt`, `rayWorld`.
- Infected: `spawnZombie()`, species AI inside `update()`.
- Main loop: `update(dt)` (game logic), `loop(now)` (frame + camera + render). Camera code is near the end of `loop`.
- Co-op: `netInit()` — only works on the Claude artifact host (uses `window.claude`); safely does nothing elsewhere.

**State objects:** `P` (player physics/actions), `S` (saved state: hp, inventory, weapon, crouch), `SOLD` (rig, mixer, layers, bones `SOLD.b`), `SET` (settings).

## The town map: Ashford (B141)
Replaced the forest. Internally it's still `FOREST_MAP` / `FOREST` / `forest*()` (so saves, fog, spawns and the map screen keep working); the save key is `holdout-save-town`.
`WORLD=250` (500 x 500 m). Layout data is the `FOREST` object: `roads` (polylines + widths), `trails` (alleys/footpaths), `clear` (open areas for fog), `dark` (wooded pockets), `lots`.
`buildForest()` builds it in sections: highway/checkpoint (spawn), gas station, motel, Main Street, water tower, residential + church, clinic, industrial, boundaries, trees, clutter.
Helpers: `townHouse`, `bgHouse`, `shop`, `bgShop`, `bgBox` (closed background buildings), `lot`, `boardSign`, `streetSign`, `picket`, `chain`, `jersey`, `container`, `dumpster`, `wreck`, `overturned`, `poles`, `streetLight`, `oakGeo`, `waterTower`, `radioTower`.
`forestRoadD(x,z)` = distance to the nearest road edge + 2.2. Instanced vegetation goes through `chunked()` (64 m chunks, frustum culled).
Planned next stages: real building art from reference images, more clutter/vegetation, interiors polish, horror lighting, optimization.

## Melee grips (B140) — adding a new melee weapon
Add one line to `WGRIP` with `g` = where the fist sits on the handle (model y; the handle runs along the model's y axis). That's all.
Optional keys: `g2` (farthest point for the second hand -> makes it two-handed automatically), `tilt` (handle angle across the palm), `roll` (blade turn),
`r` (handle radius in m; otherwise measured from the model by `handleInfo`), `tight` (0–1 extra squeeze for thin grips).
How it works: `handleInfo` measures the handle; `palmFor` puts the handle centre on the palm surface; `fingerWrap` curls each finger joint (and the thumb)
until it touches the handle, using the current skin's own bones (so every skin's hand size fits); `gripFit` pushes the handle out if any finger would poke through;
`meleeFingers` holds that pose every frame (idle, walk, run, swing, roll, vault). One-handed weapons leave the off hand to the animation.
The test suite checks every `WGRIP` weapon's finger fit on the Ranger.

## Adding Mixamo animations
reek downloads from Mixamo: **FBX Binary, Without Skin, 30 fps**. Retarget with `tools/retarget/rt.py` (headless Chromium + patched FBXLoader; it maps Mixamo bones to our UE-style names and writes into `mx_anims.json`). Paths inside the scripts point at the original dev box (`/root/work/...`) — adjust them. After retargeting, strip root travel from walk/run clips (subtract the linear pelvis drift), then wire the clip into a layer (copy how `MXR_DEF` / `mxRifleSetup` does it), time-stretch with `spd/divisor`, and test.

## Gotchas learned the hard way
- Never overwrite a bone rotation that the mixer doesn't reset each frame, or it accumulates.
- Aim math must use `AIMCAM`, not `camera` (tests and cutscenes move `camera`).
- Clamp any recoil/kick factor; `P.atk` can be large after a swap.
- The pistol/rifle layers turn off during reload; the gun drops back to the procedural hold (`weaponMesh.parent===player.sg`).
- `TEST_MAP` vs forest: animation layers run on every map; only test-only gameplay (unlimited ammo, test spawns) is gated.

## Git
Work on a branch, small commits, clear messages. Keep `main` playable — GitHub Pages serves it.
