
venv:
	: # Create venv if it doesn't exist
	test -d .venv || virtualenv .venv

install: venv
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		pip install --upgrade pip\
		pip install -r requirements.txt\
	)

diff:
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		cdktf diff rust_lambda_stack\
	)

deploy:
	: # Activate venv and install somthing inside
	. .venv/bin/activate && (\
		cdktf deploy rust_lambda_stack\
	)

clean:
	rm -rf .venv/
