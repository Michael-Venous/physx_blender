# PhysX Smoke Simulation Blender Addon

A Blender addon for running PhysX-based smoke simulations with OpenVDB output.

## Features

- **Multiple Emitter Types**: Sphere, Box, Mesh, and Particle system emitters
- **OpenVDB Output**: Simulation results are exported as .nvdb/.vdb files
- **Integrated Workflow**: Bake, stop, continue, and delete simulations directly from Blender
- **Customizable Parameters**: Control smoke density, temperature, velocity, turbulence, vorticity, and more

## Installation

1. Download the addon ZIP file
2. In Blender, go to **Edit > Preferences > Add-ons**
3. Click **Install...** and select the ZIP file
4. Enable the addon by checking the box

## Bundled Binaries

The addon requires bundled binaries (executable and libraries) to be placed in:

```
physx_smoke_addon/
├── bin/
│   ├── flow_to_nvdb_minimal    # Simulation executable
│   └── libs/                   # Shared libraries
│       ├── lib*.so
│       └── ...
```

## Usage

1. Select an object in your scene (optional, for mesh emitter type)
2. Go to the **Physics** tab in the Properties panel
3. Find the **PhysX Smoke Simulation** panel
4. Configure your simulation parameters:
   - **Emitter Type**: Choose sphere, box, mesh, or particles
   - **Smoke Parameters**: Adjust density, temperature, velocity
   - **Simulation Settings**: Set frame count, resolution, output directory
5. Click **Bake** to start the simulation
6. Once complete, the VDB files will be imported as volume objects

## Controls

| Button | Description |
|--------|-------------|
| **Bake** | Start a new simulation |
| **Stop** | Pause the current simulation |
| **Continue** | Resume a stopped simulation |
| **Delete** | Remove baked files and volume objects |

## Preferences

Access addon preferences via **Edit > Preferences > Add-ons > PhysX Smoke Simulation**:

- **Executable Path**: Override the bundled executable path
- **Library Path**: Override the bundled library path

## Requirements

- Blender 4.0 or later
- Linux (for bundled binaries)
- OpenVDB support in Blender (for volume import)

## License

See the main project repository for license information.
