import shutil

import nox


@nox.session(reuse_venv=True)
def lint(session):
	session.install('-U', '.[lint]')
	session.run('flake8', 'src/')


@nox.session(reuse_venv=True)
def doc(session):
	shutil.rmtree('docs/_build', ignore_errors=True)
	session.install('-U', '.[doc]')
	session.cd('docs')
	session.run(
		'sphinx-build',
		'-b',
		'html',
		'-W',
		'-d',
		'_build/doctrees',
		'.',
		'_build/html'
	)
