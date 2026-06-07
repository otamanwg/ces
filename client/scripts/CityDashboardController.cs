using Godot;
using System;

// Main CityDashboardController - refactored into partial classes for better maintainability
//
// Architecture:
// - CityDashboardController.Main.cs - This main coordinator file
// - CityDashboardController.UI.cs - UI elements and initialization
// - CityDashboardController.State.cs - State management and validation
// - CityDashboardController.Actions.cs - Action handlers and button events
// - CityDashboardController.Data.cs - Data management, API calls, and UI updates
// - CityDashboardController.Lifecycle.cs - Lifecycle management (_Ready, _Process, _ExitTree)
// - CityDashboardController.Onboarding.cs - Onboarding flow and police recovery
// - CityDashboardController.Character.cs - Character creation and avatar management
//
// Benefits:
// - Separation of concerns
// - Easier maintenance and testing
// - Better code organization
// - Reduced cognitive load per file
// - Improved team collaboration

public partial class CityDashboardController : Control
{
    // This main file serves as the coordinator for all partial classes
    // All implementation details are moved to specialized partial class files

    // The partial keyword allows this class to be split across multiple files
    // Each file focuses on a specific aspect of the controller's functionality
}
