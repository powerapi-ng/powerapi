<img src="https://rawgit.com/Spirals-Team/powerapi/master/resources/logo/PowerAPI-logo.png" alt="Powerapi" width="300px">

[![Join the chat at https://gitter.im/Spirals-Team/powerapi](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Spirals-Team/powerapi?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![License: BSD 3](https://img.shields.io/pypi/l/powerapi.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/powerapi-ng/powerapi/build.yml)](https://github.com/powerapi-ng/powerapi/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/powerapi)](https://pypi.org/project/powerapi/)
[![Codecov](https://codecov.io/gh/powerapi-ng/powerapi/branch/master/graph/badge.svg)](https://codecov.io/gh/powerapi-ng/powerapi)

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
* **[SelfWatts: On-the-fly Selection of Performance Events to Optimize Software-defined Power Meters](https://hal.inria.fr/hal-03173410)**: G. Fieni, R. Rouvoy, L. Seinturier. *IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing* (CCGrid). May 2021, Melbourne, Australia
* **[Power Budgeting of Big Data Applications in Container-based Clusters](https://hal.inria.fr/hal-02904300)**: J. Enes, G. Fieni, R. Expósito, R. Rouvoy, J. Tourino. *IEEE Cluster*, September 2020, Kobe, Japan
* **[SmartWatts: Self-Calibrating Software-Defined Power Meter for Containers](https://hal.inria.fr/hal-02470128)**: G. Fieni, R. Rouvoy, L. Seinturier. *IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing* (CCGrid). May 2020, Melbourne, Australia
* **[Taming Energy Consumption Variations in Systems Benchmarking](https://hal.inria.fr/hal-02403379)**: Z. Ournani, M.C. Belgaid, R. Rouvoy, P. Rust, J. Penhoat, L. Seinturier. *ACM/SPEC International Conference on Performance Engineering* (ICPE). April 2020, Edmonton, Canada
* **[WattsKit: Software-Defined Power Monitoring of Distributed Systems](https://hal.inria.fr/hal-01439889)**: M. Colmant, P. Felber, R. Rouvoy, L. Seinturier. *IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing* (CCGrid). April 2017, Spain, France
* **[Process-level Power Estimation in VM-based Systems](https://hal.inria.fr/hal-01130030)**: M. Colmant, M. Kurpicz, L. Huertas, R. Rouvoy, P. Felber, A. Sobe. *European Conference on Computer Systems* (EuroSys). April 2015, Bordeaux, France
* **[Monitoring Energy Hotspots in Software](https://hal.inria.fr/hal-01069142)**: A. Noureddine, R. Rouvoy, L. Seinturier. *Journal of Automated Software Engineering*, Springer, 2015
* **[Unit Testing of Energy Consumption of Software Libraries](https://hal.inria.fr/hal-00912613)**: A. Noureddine, R. Rouvoy, L. Seinturier. *International Symposium On Applied Computing* (SAC), March 2014, Gyeongju, South Korea
* **[Informatique : Des logiciels mis au vert](http://www.jinnove.com/Actualites/Informatique-des-logiciels-mis-au-vert)**: L. Seinturier, R. Rouvoy. *J'innove en Nord Pas de Calais*, [NFID](http://www.jinnove.com)
* **[PowerAPI: A Software Library to Monitor the Energy Consumed at the Process-Level](http://ercim-news.ercim.eu/en92/special/powerapi-a-software-library-to-monitor-the-energy-consumed-at-the-process-level)**: A. Bourdon, A. Noureddine, R. Rouvoy, L. Seinturier. *ERCIM News, Special Theme: Smart Energy Systems*, 92,  pp.43-44. [ERCIM](http://www.ercim.eu), 2013
* **[Mesurer la consommation en énergie des logiciels avec précision](http://www.lifl.fr/digitalAssets/0/807_01info_130110_16_39.pdf)**: A. Bourdon, R. Rouvoy, L. Seinturier. *01 Business & Technologies*, 2013
* **[A review of energy measurement approaches](https://hal.inria.fr/hal-00912996v2)**: A. Noureddine, R. Rouvoy, L. Seinturier. *ACM SIGOPS Operating Systems Review*, ACM, 2013, 47 (3)
* **[Runtime Monitoring of Software Energy Hotspots](https://hal.inria.fr/hal-00715331)**: A. Noureddine, A. Bourdon, R. Rouvoy, L. Seinturier. *International Conference on Automated Software Engineering* (ASE), September 2012, Essen, Germany
* **[A Preliminary Study of the Impact of Software Engineering on GreenIT](https://hal.inria.fr/hal-00681560)**: A. Noureddine, A. Bourdon, R. Rouvoy, L. Seinturier. *International Workshop on Green and Sustainable Software* (GREENS), June 2012, Zurich, Switzerland

## Use Cases
PowerAPI is used in a variety of projects to address key challenges of GreenIT:
* [SmartWatts](https://github.com/powerapi-ng/smartwatts-formula) is a self-adaptive power meter that can estimate the energy consumption of software containers in real-time.
* [GenPack](https://hal.inria.fr/hal-01403486) provides a container scheduling strategy to minimize the energy footprint of cloud infrastructures.
* [VirtualWatts](https://github.com/powerapi-ng/virtualwatts-formula) provides process-level power estimation of applications running in virtual machines.
* [Web Energy Archive](http://webenergyarchive.com) ranks popular websites based on the energy footpring they imposes to browsers.
* [Greenspector](https://greenspector.com) optimises the power consumption of software by identifying potential energy leaks in the source code.

## License
PowerAPI is licensed under the BSD-3-Clause License. See the [LICENSE](LICENSE) file for details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fpowerapi-ng%2Fpowerapi.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Fpowerapi-ng%2Fpowerapi?ref=badge_large)
