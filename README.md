# `tini.flow` -- Hey, everybody is still dealing with Shell-scripts...

Shell is powerful, simple, and universal. But Shell is also obscure, baroque, and severely limited. Yet, it is often the most natural way to solve common automation problems.
Stepping back, Shell scripts are one of the most common ways to implement workflows. Building workflows is a critical and core component of automation.
The use of Shell for workflows is often criticized as being ‘quick and dirty’, as Shell's unique power, convenience, and flexibility is burdened by certain serious limitations (a consequence of the history and necessity for backwards-compatibility of common Shells).
This talk will show that it is possible to address the limitations of Shell without throwing away its power, convenience, and flexibility and will present tini.flow, a Python-based attempt to implement these ideas.

[Presentation describing the tool](https://docs.google.com/presentation/d/1bfcQeQ3qP9rOjXUJcNCzyErVgC5JbrT8HX6wdmRInbs/edit?usp=sharing)

## Getting Started

For example workflows through the `/example` folder. Some more detailed tutorials will follow later.

### Prerequisites

Python 3.6 or higher

ZSh if you don't want to change the wrapper scripts and env..

### Installing

Not part of any package managers yet, but just clone the repo and get started as long as above dependencies are satisfied.

## Running the tests

`make.flow` encodes all the current testing functionality. The 'watch' targets are especially useful in this regards, as they rerun the chosen test(s) on every change of the `tiniflow/*.py`-files
## Authors

* **Titus von Köller** <!-- - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth) -->

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

<!-- ## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
-->
