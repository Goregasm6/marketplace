import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.database import initialize
from analysis.flipscore import calculate


initialize()


test_listing={

"title":
"Vintage Fender tube amp needs repair",

"description":
"old garage find untested",

"price":
50

}


print(
calculate(test_listing)
)