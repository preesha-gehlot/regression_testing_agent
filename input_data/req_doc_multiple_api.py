REQUIREMENTS_SPEC_DOC = """
The current Journey Results API returns a list of possible journeys with varying levels of detail. 
Users need the ability to specify their accessibility preferences for the journeys provided. 

We want to add a new query parameter accessibilityPreference to the existing /Journey/JourneyResults/{from}/to/{to} endpoint. 

PARAMETER SPECIFICATION:
    - Type: array of strings (enum)
    - Required: false
    - Location: query parameter
    - Format: comma-separated list (exploded)
    - Description: The accessibility preference must be a comma separated list eg. "noSolidStairs,noEscalators,noElevators,stepFreeToVehicle,stepFreeToPlatform"

ALLOWED VALUES:
    - NoRequirements - No specific accessibility requirements
    - NoSolidStairs - Avoid routes with solid stairs
    - NoEscalators - Avoid routes with escalators
    - NoElevators - Avoid routes with elevators
    - StepFreeToVehicle - Ensure step-free access to vehicles
    - StepFreeToPlatform - Ensure step-free access to platforms       
"""
