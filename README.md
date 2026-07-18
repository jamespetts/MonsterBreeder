# Monster Breeder

**Breed a population of monsters to defend ancient treasure.**

Monster Breeder is a browser-based strategy and simulation game about maintaining a single interbreeding monster population. Across seasonal management and real-time raid phases, you breed and deploy monsters, respond to injuries and food shortages, introduce wild genes, and try to preserve the kingdom's scattered treasure from increasingly capable adventurers.

> **Project status:** Monster Breeder is under active development. Features, balance and save compatibility may change.

## Gameplay

Each season alternates between two broad phases:

1. **Monster management** - inspect the population, choose breeding pairs, allocate food, review injuries and ancestry, and decide which monsters to deploy.
2. **Raid simulation** - watch monsters, adventurers and wildlife act autonomously in a procedurally generated landscape, while capturing, recalling or releasing monsters when appropriate.

Monster Breeder does not use fixed fantasy species as collectible units. Instead, monsters belong to one interbreeding population whose characteristics emerge from inherited genes, mutation, selection and environmental pressure. Breeding decisions therefore shape both individual offspring and the long-term viability of the population.

## Main features

- Detailed genetic inheritance covering colour, metabolism, morphology, behaviour, perception and reproduction.
- Emergent phenotypes with dominance, codominance and genetic crossover.
- Seasonal breeding, eggs, juvenile growth, ageing and old-age mortality.
- Pedigrees and interactive family trees.
- Nutrition, fat reserves, purchased food and treasure-funded emergency feeding.
- Injuries, disease, fatigue, thermal stress and long-term performance records.
- Procedurally generated terrain, climate, biomes and hydrology.
- Autonomous monsters, adventurers and wildlife with pathfinding, perception, morale and combat behaviour.
- Wild-monster capture and release, allowing new genes to enter the breeding population.
- Multiple adventurer classes with different capabilities and priorities.
- Campaign statistics, scoreboards, round histories and local leaderboards.
- Save/load support and portable JSON monster import/export.
- An in-game tutorial and the diegetic **Book of Monster Husbandry**.

## Game modes

- **Tutorial** - guided introduction to the central controls and systems.
- **Campaign** - a persistent 25-round campaign.
- **Advanced Campaign** - a 20-round campaign with additional setup options.
- **Quick Game** - start a standalone game quickly.
- **Custom Game** - choose the world seed, map size, biome and starting treasure.

Custom worlds range from compact test maps to very large landscapes. Larger maps require more processing time and memory.

## Controls

Most actions are available through the on-screen interface. The raid map supports mouse and touch navigation.

### Map navigation

- **Drag:** pan the map
- **Mouse wheel or pinch:** zoom
- **Click/tap:** inspect or interact with an object
- **Arrow keys:** move the camera

### Keyboard shortcuts

- `Q` - inspect/query mode
- `C` - capture a wild monster
- `B` - recall a captured monster to base
- `R` - release a captured monster
- `Space` - pause or resume
- `F` - toggle fast forward
- `S` - open the scoreboard
- `Esc` - return to the main menu

Breeding can also be arranged by dragging one compatible monster portrait onto another in Monster Management.

## Running the game

Monster Breeder is currently maintained as a single main HTML file and runs entirely in a modern web browser.

### Simple method

Open `index.html` in a current version of Firefox, Chrome, Edge or another modern browser.

### Local web-server method

If browser security restrictions prevent workers, audio or local resources from loading, serve the repository over HTTP. For example, if Python 3 is installed:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/
```

No build step is required.

## Saving and monster transfers

Saved games and campaign leaderboards are stored locally by the browser. Clearing site data or using a different browser profile may remove them.

Individual monsters can be exported as JSON transfer files and imported into another game. Keep exported records somewhere safe if they are intended for long-term preservation.

Save data is versioned and includes migration support for older supported formats, but this remains a developing project. Retaining separate backups before updating is advisable.

## Repository structure

The project is deliberately kept primarily in one HTML file:

```text
index.html    Game UI, rendering, simulation worker and game logic
music/        Background music resources, where supplied
```

The simulation runs in a Web Worker. Authoritative game state remains in the simulation, while the browser's main thread handles rendering, input and interface presentation.

## Development principles

The codebase follows several architectural rules:

- Persistent world facts have one authoritative mutable representation.
- `World` owns persistent physical-place data.
- `GameState` owns persistent player monsters, eggs and campaign statistics.
- `Raid` owns temporary live raid state.
- Agents own their movement, pathfinding and perception behaviour.
- Save files serialise authoritative simulation state rather than transient rendering state.
- Map-dependent systems must work across variable world sizes rather than rely on one fixed map.

Please preserve the single-file architecture unless there is an agreed reason to change it.

## Contributing

Bug reports, balance observations and focused pull requests are welcome. When reporting a problem, please include:

- browser and version;
- game mode, round and season;
- world seed and map size, where relevant;
- steps required to reproduce the problem;
- any console errors; and
- a save or exported monster file where it helps reproduce the issue.

Before committing, check that generated files, local saves, credentials and other private material are not included.

## Licence

The source code declares the following SPDX licence identifier:

```text
GPL-3.0-only
```

See the repository's `LICENSE` file for the complete licence text. If the repository does not yet contain that file, add a copy of the GNU General Public License version 3 before publishing the project.
