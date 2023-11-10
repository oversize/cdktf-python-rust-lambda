
venv:
	: # Create venv if it doesn't exist
	: # test -d venv || virtualenv -p python3 --no-site-packages venv
	test -d .venv || python3 -m venv .venv

install: venv
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		pip install --upgrade pip\
		pip install -r requirements.txt\
	)

diff:
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		cdktf diff offchain-metadata-lambda\
	)

deploy:
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		cdktf deploy offchain-metadata-lambda\
	)

clean:
	rm -rf .venv/
