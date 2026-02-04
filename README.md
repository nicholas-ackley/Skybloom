# SkyBloom 

**SkyBloom** A Stardew -inspired sandbox adventure where players cultivate life on floating islands! 
            Master procedural farming, interact with a cast of unique NPCs, and uncover the mystery 
            of the floating world through a narrative driven Story Mode.



## Core Gameplay
* **Momentum-Based Movement**: Custom player controller physics focusing on air-strafing and "weighty" platforming.
* **Environmental Storytelling**: Hand-crafted levels that reveal the history of the SkyBloom world through background details and level design.
* **Modular Combat**: A flexible enemy system designed to test player reflexes and positioning.

## 🛠️ Technical Implementation
* **Engine**: Godot 4.x (GDScript)
* **Design Patterns**: Heavy use of **Signals** and **Composition** to keep nodes decoupled and maintainable.
* **State Machines**: Implemented a robust hierarchical state machine to manage complex player animations and transitions (Idle, Dash, Wall-Cling, Attack).
* **Parallax Systems**: Multi-layered background rendering to create depth in a 2D space.

## 🚀 Key Learning Outcomes
Developing SkyBloom served as a practical application of the concepts discussed in my **Object-Oriented Programming** research. Key takeaways included:
1. **Performance Optimization**: Efficiently managing collision layers and bitmasks to maintain 60 FPS across varied hardware.
2. **Resource Management**: Utilizing Godot’s `.tres` (Resource) files to store enemy stats and item data, allowing for easy balancing without touching the core logic.
3. **UI/UX**: Designing a minimalist, "diegetic" HUD that keeps the player focused on the action while providing essential feedback.

## 📦 Installation & Running
1. **Clone the repo**:
   ```bash
   git clone [https://github.com/nicholas-ackley/skybloom.git](https://github.com/nicholas-ackley/skybloom.git)
