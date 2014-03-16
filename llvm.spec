Summary:	Low Level Virtual Machine
Name:		llvm
Version:	3.4
Release:	3
License:	University of Illinois/NCSA Open Source License
Group:		Development/Languages
Source0:	http://llvm.org/releases/%{version}/%{name}-%{version}.src.tar.gz
# Source0-md5:	46ed668a1ce38985120dbf6344cf6116
Source1:	http://llvm.org/releases/%{version}/clang-%{version}.src.tar.gz
# Source1-md5:	b378f1e2c424e03289effc75268d3d2c
Source2:	http://llvm.org/releases/%{version}/compiler-rt-%{version}.src.tar.gz
# Source2-md5:	7938353e3a3bda85733a165e7ac4bb84
Patch0:		%{name}-preserve-timestamp.patch
Patch1:		%{name}-linker.patch
Patch2:		%{name}-freddix.patch
URL:		http://llvm.org/
BuildRequires:	bash
BuildRequires:	bison
BuildRequires:	flex
BuildRequires:	groff
BuildRequires:	libltdl-devel
BuildRequires:	libstdc++-devel
Requires:	%{name}-libs = %{version}-%{release}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sysconfdir	/etc/%{name}

# strip corrupts: $RPM_BUILD_ROOT/usr/lib64/llvm-gcc/bin/llvm-c++ ...
%define		_noautostrip	.*/\\(libmud.*\\.a\\|bin/llvm-.*\\|lib.*++\\.a\\)

%description
LLVM is a compiler infrastructure designed for compile-time,
link-time, runtime, and idle-time optimization of programs from
arbitrary programming languages. LLVM is written in C++ and has been
developed since 2000 at the University of Illinois and Apple. It
currently supports compilation of C and C++ programs, using front-ends
derived from GCC 4.0.1. A new front-end for the C family of languages
is in development. The compiler infrastructure includes mirror sets of
programming tools as well as libraries with equivalent functionality.

%package libs
Summary:	LLVM library
Group:		Libraries

%description libs
This package contains LLVM library.

%package devel
Summary:	Libraries and header files for LLVM
Group:		Development/Languages
Requires:	%{name} = %{version}-%{release}

%description devel
This package contains library and header files needed to develop new
native programs that use the LLVM infrastructure.

%package clang
Summary:	A C language family frontend for LLVM
License:	NCSA
Group:		Development/Languages

%description clang
clang: noun 1. A loud, resonant, metallic sound. 2. The strident call
of a crane or goose. 3. C-language family front-end toolkit.

%package clang-analyzer
Summary:	A source code analysis framework
License:	NCSA
Group:		Development/Languages
Requires:	%{name}-clang = %{version}-%{release}
Requires:	python

%description clang-analyzer
The Clang Static Analyzer consists of both a source code analysis
framework and a standalone tool that finds bugs in C and Objective-C
programs. The standalone tool is invoked from the command-line, and is
intended to run in tandem with a build of a project or code base.

%package clang-devel
Summary:	Header files for clang
Group:		Development/Languages
Requires:	%{name}-clang = %{version}-%{release}

%description clang-devel
This package contains header files for the Clang compiler.

%prep
%setup -q -a1 -a2
mv clang-%{version} tools/clang
mv compiler-rt-%{version} projects/compiler-rt
%patch0 -p1
%patch1 -p1
%patch2 -p1

# configure does not properly specify libdir
%{__sed} -i 's|(PROJ_prefix)/lib|(PROJ_prefix)/%{_lib}|g' Makefile.config.in
%{__sed} -i 's|/lib /usr/lib $lt_ld_extra|%{_libdir} $lt_ld_extra|' ./configure
%{__sed} -i 's|/lib\>|/%{_lib}|g' tools/llvm-config/llvm-config.cpp

grep -rl /usr/bin/env tools utils | xargs sed -i -e '1{
	s,^#!.*bin/env python,#!%{__python},
	s,^#!.*bin/env perl,#!%{__perl},
}'

install -d obj

%build
export CC="%{__cc}"
export CXX="%{__cxx}"

# Disabling assertions now, rec. by pure and needed for OpenGTL
# TESTFIX no PIC on ix86: http://llvm.org/bugs/show_bug.cgi?id=3801
#
# bash specific 'test a < b'
cd obj
bash ../%configure \
	--datadir=%{_datadir}/%{name}-%{version}	\
	--libdir=%{_libdir}/%{name}	\
	--disable-assertions		\
	--disable-debug-runtime		\
	--disable-expensive-checks	\
	--disable-libcpp		\
	--disable-polly			\
	--disable-static		\
	--enable-bindings=none		\
	--enable-experimental-targets=R600  \
	--enable-jit			\
	--enable-libffi			\
	--enable-optimized		\
	--enable-shared			\
	--with-binutils-include=%{_includedir}	\
	--with-optimize-option="%{rpmcflags} %{rpmcppflags}"

%{__make} \
	REQUIRES_RTTI=1	\
	VERBOSE=1

%install
rm -rf $RPM_BUILD_ROOT
%{__make} -C obj -j1 install \
	PROJ_docsdir=/moredocs \
	DESTDIR=$RPM_BUILD_ROOT

# Static analyzer not installed by default:
# http://clang-analyzer.llvm.org/installation#OtherPlatforms
install -d $RPM_BUILD_ROOT%{_libdir}/clang-analyzer
# create launchers
for f in scan-{build,view}; do
	ln -s %{_libdir}/clang-analyzer/$f/$f $RPM_BUILD_ROOT%{_bindir}/$f
	cp -pr tools/clang/tools/$f $RPM_BUILD_ROOT%{_libdir}/clang-analyzer
done

rm -v $RPM_BUILD_ROOT%{_libdir}/*LLVMHello.*

# Move documentation back to build directory
rm -rf moredocs
mv $RPM_BUILD_ROOT/moredocs .
rm -fv moredocs/*.tar.gz
rm -fv moredocs/ocamldoc/html/*.tar.gz

%clean
rm -rf $RPM_BUILD_ROOT

%post	libs -p /usr/sbin/ldconfig
%postun	libs -p /usr/sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc CREDITS.TXT LICENSE.TXT README.txt
%attr(755,root,root) %{_bindir}/bugpoint
%attr(755,root,root) %{_bindir}/llc
%attr(755,root,root) %{_bindir}/lli*
%attr(755,root,root) %{_bindir}/opt
%attr(755,root,root) %{_bindir}/llvm-*
%attr(755,root,root) %{_bindir}/macho-dump
%exclude %attr(755,root,root) %{_bindir}/llvm-config
%if 0
%{_mandir}/man1/bugpoint.1*
%{_mandir}/man1/llc.1*
%{_mandir}/man1/lli.1*
%{_mandir}/man1/llvm-*.1*
%{_mandir}/man1/opt.1*
%{_mandir}/man1/tblgen.1*
%endif

%files libs
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/libLLVM-*.*.so

%files devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/llvm-config
%attr(755,root,root) %{_libdir}/BugpointPasses.so
%attr(755,root,root) %{_libdir}/LLVMgold.so
%attr(755,root,root) %{_libdir}/libLTO.so
%{_includedir}/llvm
%{_includedir}/llvm-c
%{_libdir}/lib*.a

%files clang
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/clang*
%attr(755,root,root) %{_libdir}/libclang.so
%{_prefix}/lib/clang
%{_mandir}/man1/clang.1.*

%files clang-analyzer
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/scan-build
%attr(755,root,root) %{_bindir}/scan-view
%dir %{_libdir}/clang-analyzer

%dir %{_libdir}/clang-analyzer/scan-view
%attr(755,root,root) %{_libdir}/clang-analyzer/scan-view/scan-view
%{_libdir}/clang-analyzer/scan-view/Resources
%{_libdir}/clang-analyzer/scan-view/*.py

%dir %{_libdir}/clang-analyzer/scan-build
%{_libdir}/clang-analyzer/scan-build/*.css
%{_libdir}/clang-analyzer/scan-build/*.js
%attr(755,root,root) %{_libdir}/clang-analyzer/scan-build/scan-build
%attr(755,root,root) %{_libdir}/clang-analyzer/scan-build/*-analyzer

%files clang-devel
%defattr(644,root,root,755)
%{_includedir}/clang
%{_includedir}/clang-c

