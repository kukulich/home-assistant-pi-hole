"""Constants for Pi-hole V6."""

from datetime import timedelta

DOMAIN = "pi_hole_v6"
DEFAULT_NAME = "Pi-Hole"
# DEFAULT_URL = "https://pi.hole:443/api"
DEFAULT_URL = "http://nipogi.local:8088/api"
DEFAULT_PASSWORD = "+lOoe/SvjmjzM4LGOzRynRIF69AvqyR2719BYV8rWhw="

SERVICE_DISABLE = "disable"
SERVICE_DISABLE_ATTR_DURATION = "duration"
SERVICE_ENABLE = "enable"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)
