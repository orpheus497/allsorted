#!/usr/bin/env python3
"""
Custom classification rules example for allsorted.

This script demonstrates how to add custom file classification rules
for organizing specialized file types.

Created by orpheus497
"""

from pathlib import Path
from allsorted.config import Config
from allsorted.planner import OrganizationPlanner
from allsorted.executor import OrganizationExecutor


def organize_with_custom_rules(directory_path: str) -> None:
    """
    Organize a directory with custom classification rules.

    Args:
        directory_path: Path to directory to organize
    """
    # Create configuration
    config = Config()

    # Add custom rules for data science files
    config.add_classification_rule(
        category="Code",
        subcategory="DataScience",
        extensions=[".ipynb", ".rmd", ".qmd", ".r"]
    )

    # Add custom rules for CAD files
    config.add_classification_rule(
        category="Docs",
        subcategory="CAD",
        extensions=[".dwg", ".dxf", ".stl", ".obj", ".fbx"]
    )

    # Add custom rules for game development
    config.add_classification_rule(
        category="Code",
        subcategory="GameDev",
        extensions=[".unity", ".unitypackage", ".prefab", ".mat"]
    )

    # Add custom rules for blockchain/crypto
    config.add_classification_rule(
        category="Code",
        subcategory="Blockchain",
        extensions=[".sol", ".vy"]  # Solidity and Vyper
    )

    # Add custom rules for machine learning models
    config.add_classification_rule(
        category="System",
        subcategory="MLModels",
        extensions=[".h5", ".keras", ".pkl", ".joblib", ".model"]
    )

    print("Custom classification rules added:")
    print("  - DataScience: .ipynb, .rmd, .qmd, .r")
    print("  - CAD: .dwg, .dxf, .stl, .obj, .fbx")
    print("  - GameDev: .unity, .unitypackage, .prefab, .mat")
    print("  - Blockchain: .sol, .vy")
    print("  - MLModels: .h5, .keras, .pkl, .joblib, .model")
    print()

    # Create planner and executor
    planner = OrganizationPlanner(config)
    root_dir = Path(directory_path).resolve()

    print(f"Organizing directory: {root_dir}")

    # Create and execute plan
    plan = planner.create_plan(root_dir)
    print(f"Found {len(plan.operations)} file operations")

    # Show which custom categories will be created
    custom_categories = set()
    for operation in plan.operations:
        dest_parts = operation.destination.parts
        if "all_Code" in dest_parts:
            idx = dest_parts.index("all_Code")
            if idx + 1 < len(dest_parts):
                subcategory = dest_parts[idx + 1]
                if subcategory in ["DataScience", "GameDev", "Blockchain"]:
                    custom_categories.add(subcategory)
        elif "all_System" in dest_parts:
            idx = dest_parts.index("all_System")
            if idx + 1 < len(dest_parts):
                if dest_parts[idx + 1] == "MLModels":
                    custom_categories.add("MLModels")
        elif "all_Docs" in dest_parts:
            idx = dest_parts.index("all_Docs")
            if idx + 1 < len(dest_parts):
                if dest_parts[idx + 1] == "CAD":
                    custom_categories.add("CAD")

    if custom_categories:
        print(f"Custom categories to be created: {', '.join(sorted(custom_categories))}")
    else:
        print("No files matching custom rules found")

    # Ask for confirmation
    response = input("\nProceed with organization? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled")
        return

    # Execute
    executor = OrganizationExecutor(dry_run=False, log_operations=True)
    result = executor.execute_plan(plan)

    print(f"\nOrganization complete!")
    print(f"Files moved: {result.files_moved}")
    print(f"Success rate: {result.success_rate:.1f}%")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python custom_rules.py <directory>")
        print("\nThis script adds custom classification rules for:")
        print("  - Data science notebooks and R scripts")
        print("  - CAD and 3D model files")
        print("  - Game development assets")
        print("  - Blockchain smart contracts")
        print("  - Machine learning model files")
        sys.exit(1)

    directory = sys.argv[1]

    try:
        organize_with_custom_rules(directory)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
