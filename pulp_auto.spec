Name:		pulp_auto
Version:	0.12
Release:	1%{?dist}
Summary:	Pulp REST API automation library and test cases

Group:		Development/Tools
License:	GPLv3+
URL:		https://github.com/RedHatQE/pulp-automation
Source0:	%{name}-%{version}.tar.gz
BuildArch:  	noarch

BuildRequires:	python-devel
Requires:	python-nose, python-gevent, python-qpid, PyYAML, python-stitches

%description
%{summary}

%prep
%setup -q

%build

%install
%{__python} setup.py install --single-version-externally-managed -O1 --root $RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc LICENSE README.md
%{python_sitelib}/*.egg-info
%{python_sitelib}/%{name}/*.py*
%{python_sitelib}/%{name}/handler/*.py*
%{python_sitelib}/%{name}/units/*.py*
%{python_sitelib}/%{name}/consumer/*.py*
%dir %{_datadir}/%{name}/tests
%attr(0644, root, root) %{_datadir}/%{name}/tests/*.py
%attr(0644, root, root) %{_datadir}/%{name}/tests/inventory.yml
%attr(0644, root, root) %{_datadir}/%{name}/tests/.coveragerc
%exclude %{_datadir}/%name/tests/*.py?

%changelog
* Tue Dec 03 2013 dparalen <vetrisko@gmail.com> 0.12-1
- bump version (vetrisko@gmail.com)
- full git update (vetrisko@gmail.com)
- fix: buildslave start command (vetrisko@gmail.com)
- fix: redirection is preserved (vetrisko@gmail.com)
- fix: sudo has to be 'interactive' (vetrisko@gmail.com)
- fix: exec as a buildbot user (vetrisko@gmail.com)
- fix: tests require insecure broker (vetrisko@gmail.com)
- fix: always create receiver queues (vetrisko@gmail.com)
- add qpid-tools package (vetrisko@gmail.com)
- fix: allow port 8010 (vetrisko@gmail.com)
- fix: updates and packages; custom pulp repo (vetrisko@gmail.com)
- fix: custom pulp repo; yum updates (vetrisko@gmail.com)
- fix: failing steps have to stop build; mutual exclusivity of steps introduced
  (vetrisko@gmail.com)
- buildbot deployment (vetrisko@gmail.com)
- introducing master.cfg (vetrisko@gmail.com)

* Mon Nov 11 2013 dparalen <vetrisko@gmail.com> 0.11-1
- fix: avoid racecondition giving ssl cert errors for one of the greenlets here
  (vetrisko@gmail.com)
- fix: attribute name (vetrisko@gmail.com)
- enhancing gevent.monkey.patch-ing (vetrisko@gmail.com)
- fix: attr error in case different types of objects are being compared
  (vetrisko@gmail.com)

* Sun Nov 10 2013 dparalen <vetrisko@gmail.com> 0.10-1
- 

* Sun Nov 10 2013 dparalen <vetrisko@gmail.com> 0.9-1
- new package built with tito
