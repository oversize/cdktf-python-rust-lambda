# A Python lambda deployed with CDKTF

This project implements a lambda function in rust that is deployed
to aws using the cdktf in python. The lambda does not do anything
particularly usefull since the main goal here is to show how to get it
done with the cdktf.

The code for CDKTF is in `infra/` and the code for the actual lambda in `myrustlambda/`.

## Requirements

Before using this you need to have cdktf installed. Also a basic understanding
of how the cdktf works and what is does will be very helpfull. You should go read
their docs: <https://developer.hashicorp.com/terraform/tutorials/cdktf/cdktf-install>.

To develop/build the lambda you need to have the rust toolchain installed. Go
to <https://rustup.rs/> and/or <https://www.rust-lang.org/> to get you started.

After cloning this repository, you will need to create a virtual environemt
and install the requirements using pip.

But wait, cdktf is written in node and installed via npm??
Yes, but we are writing the CDKTF COde in python (because i dont know TS).
So we need to install the python packages/bindings for cdktf that can generate
terraform from python.

* <https://pypi.org/project/cdktf/> cdktf for python itself
* <https://pypi.org/project/cdktf-cdktf-provider-aws/> aws provider to build aws resources


```bash
python -m venv .venv
source ./venb/bin/activate
# optional upgrade pip
pip install -U pip
# Install requirements
pip install -r requirements.txt
```

When you use the `cdktf init` command it will generate a project UUID for you.
But i assume you cloned this repository and thus have not done so. Before
moving on you should generate one such id for yourself and store it in
the cdktf.json file.

```bash
# generate uuid in bash using python
python -c 'import uuid; print(uuid.uuid4())'
```

This will print a UUID like this one `9e21d261-dc59-443a-aa55-6cef44ac5a87`.
Copy that and insert it into your cdktf.json in the dield `projectId`.


