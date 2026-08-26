import logging
import warnings
from rich.console import Console

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SecToolkit")

console = Console()