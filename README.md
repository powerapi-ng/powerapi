<img src="https://rawgit.com/Spirals-Team/powerapi/master/resources/logo/PowerAPI-logo.png" alt="Powerapi" width="300px">

[![License: BSD 3](https://img.shields.io/pypi/l/powerapi.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/powerapi-ng/powerapi/build.yml)](https://github.com/powerapi-ng/powerapi/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/powerapi)](https://pypi.org/project/powerapi/)
[![Codecov](https://codecov.io/gh/powerapi-ng/powerapi/branch/master/graph/badge.svg)](https://codecov.io/gh/powerapi-ng/powerapi)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.11453194.svg)](https://doi.org/10.5281/zenodo.11453194)
[![JOSS paper](https://joss.theoj.org/papers/ff5876ca096c62cb6d243e56b5676c4e/status.svg)](https://joss.theoj.org/papers/ff5876ca096c62cb6d243e56b5676c4e)

PowerAPI is a middleware toolkit for building software-defined power meters.
Software-defined power meters are configurable software libraries that can estimate the power consumption of software in real-time.
PowerAPI supports the acquisition of raw metrics from a wide diversity of sensors (*eg.*, physical meters, processor interfaces, hardware counters, OS counters) and the delivery of power consumptions via different channels (including file system, network, web, graphical).
As a middleware toolkit, PowerAPI offers the capability of assembling power meters *«à la carte»* to accommodate user requirements.

# About

PowerAPI is an open-source project developed by the [Spirals project-team](https://team.inria.fr/spirals), a joint research group between the [University of Lille](https://www.univ-lille.fr) and [Inria](https://www.inria.fr).

The documentation of the project is available [here](http://powerapi.org).

## Mailing list
You can follow the latest news and asks questions by subscribing to our <a href="mailto:sympa@inria.fr?subject=subscribe powerapi">mailing list</a>.

## Contributing
If you would like to contribute code you can do so through GitHub by forking the repository and sending a pull request.

When submitting code, please make every effort to [follow existing conventions and style](CONTRIBUTING.md) in order to keep the code as readable as possible.

## Publications
- **[PowerAPI: A Python framework for building software-defined power meters](https://joss.theoj.org/papers/10.21105/joss.06670)**: G. Fieni, D. Romero Acero, P. Rust, R. Rouvoy. _Journal of Open Source Software_ (JOSS). The Open Journal, June 2024.
- **[Evaluating the Impact of Java Virtual Machines on Energy Consumption](https://hal.inria.fr/hal-03275286v1)**: Z. Ournani, MC. Belgaid, R. Rouvoy, P. Rust, J. Penhoat. _15th ACM/IEEE International Symposium on Empirical Software Engineering and Measurement_ (ESEM). October 2021, Bari, Italy.
- **[SelfWatts: On-the-fly Selection of Performance Events to Optimize Software-defined Power Meters](https://hal.inria.fr/hal-03173410v1)**: G. Fieni, R. Rouvoy, L. Seiturier. _20th IEEE/ACM International Symposium on Cluster, Cloud and Internet Computing_ (CCGRID 2021). May 2021, Melbourne, Australia.
- **[SmartWatts: Self-Calibrating Software-Defined Power Meter for Containers](https://hal.inria.fr/hal-02470128v1)**: G. Fieni, R. Rouvoy, L. Seiturier. _20th IEEE/ACM International Symposium on Cluster, Cloud and Internet Computing_ (CCGRID 2020). May 2020, Melbourne, Australia.
- **[Taming Energy Consumption Variations in Systems Benchmarking](https://hal.inria.fr/hal-02403379v1)**: Z. Ournani, MC. Belgaid, R. Rouvoy, P. Rust, J. Penhoat, L. Seinturier. _11th ACM/SPEC International Conference on Performance Engineering_ (ICPE'2020). April 2020, Edmonton, Canada.
- **[The Next 700 CPU Power Models](https://hal.inria.fr/hal-01827132v2)**: M. Colmant, R. Rouvoy, M. Kurpicz, A. Sobe, P. Felber, L. Seinturier. _Elsevier Journal of Systems and Software_ (JSS). 144(10):382-396, Elsevier.
- **[WattsKit: Software-Defined Power Monitoring of Distributed Systems](https://hal.inria.fr/hal-01439889)**: M. Colmant, P. Felber, R. Rouvoy, L. Seinturier. _IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing_ (CCGrid). April 2017, Spain, France. pp.1-14.
- **[Process-level Power Estimation in VM-based Systems](https://hal.inria.fr/hal-01130030)**: M. Colmant, M. Kurpicz, L. Huertas, R. Rouvoy, P. Felber, A. Sobe. _European Conference on Computer Systems_ (EuroSys). April 2015, Bordeaux, France. pp.1-14.
- **[Monitoring Energy Hotspots in Software](https://hal.inria.fr/hal-01069142)**: A. Noureddine, R. Rouvoy, L. Seinturier. _Journal of Automated Software Engineering_, Springer, 2015, pp.1-42.
- **[Unit Testing of Energy Consumption of Software Libraries](https://hal.inria.fr/hal-00912613)**: A. Noureddine, R. Rouvoy, L. Seinturier. _International Symposium On Applied Computing_ (SAC), March 2014, Gyeongju, South Korea. pp.1200-1205.
- **[Informatique : Des logiciels mis au vert](http://www.jinnove.com/Actualites/Informatique-des-logiciels-mis-au-vert)**: L. Seinturier, R. Rouvoy. _J'innove en Nord Pas de Calais_, [NFID](http://www.jinnove.com), 2013.
- **[PowerAPI: A Software Library to Monitor the Energy Consumed at the Process-Level](http://ercim-news.ercim.eu/en92/special/powerapi-a-software-library-to-monitor-the-energy-consumed-at-the-process-level)**: A. Bourdon, A. Noureddine, R. Rouvoy, L. Seinturier. _ERCIM News, Special Theme: Smart Energy Systems_, 92, pp.43-44. [ERCIM](http://www.ercim.eu), 2013.
- **[Mesurer la consommation en énergie des logiciels avec précision](http://www.lifl.fr/digitalAssets/0/807_01info_130110_16_39.pdf)**: A. Bourdon, R. Rouvoy, L. Seinturier. _01 Business & Technologies_, 2013.
- **[A review of energy measurement approaches](https://hal.inria.fr/hal-00912996v2)**: A. Noureddine, R. Rouvoy, L. Seinturier. _ACM SIGOPS Operating Systems Review_, ACM, 2013, 47 (3), pp.42-49.
- **[Runtime Monitoring of Software Energy Hotspots](https://hal.inria.fr/hal-00715331)**: A. Noureddine, A. Bourdon, R. Rouvoy, L. Seinturier. _International Conference on Automated Software Engineering_ (ASE), September 2012, Essen, Germany. pp.160-169.
- **[A Preliminary Study of the Impact of Software Engineering on GreenIT](https://hal.inria.fr/hal-00681560)**: A. Noureddine, A. Bourdon, R. Rouvoy, L. Seinturier. _International Workshop on Green and Sustainable Software_ (GREENS), June 2012, Zurich, Switzerland. pp.21-27.

## Use Cases
PowerAPI is used in a variety of projects to address key challenges of GreenIT:
* [SmartWatts](https://github.com/powerapi-ng/smartwatts-formula) is a self-adaptive power meter that can estimate the energy consumption of software containers in real-time.
* [GenPack](https://hal.inria.fr/hal-01403486) provides a container scheduling strategy to minimize the energy footprint of cloud infrastructures.
* [VirtualWatts](https://github.com/powerapi-ng/virtualwatts-formula) provides process-level power estimation of applications running in virtual machines.
* [Web Energy Archive](http://webenergyarchive.com) ranks popular websites based on the energy footpring they imposes to browsers.
* [Greenspector](https://greenspector.com) optimises the power consumption of software by identifying potential energy leaks in the source code.

## Research Projects

Currently, PowerAPI is used in two research projects:

- [Distiller ANR Project](https://www.davidson.fr/blog/comment-reduire-limpact-environnemental-des-applications-cloud-davidson-consulting-inria-ovhcloud-orange-sassocient-pour-le-programme-de-recherche-distiller) that searches to reduce energy consumption of Cloud applications.
- [Défi Pulse](https://www.inria.fr/fr/pulse-defi-qarnot-computing-ademe-calcul-intensif-hpc-environnement) studies how to valorize emissions from High Performance Computing (HPC) using as use case [Qarnot Computing's](https://qarnot.com/en) offers.

## License
PowerAPI is licensed under the BSD-3-Clause License. See the [LICENSE](LICENSE) file for details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fpowerapi-ng%2Fpowerapi.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fpowerapi-ng%2Fpowerapi?ref=badge_large)
