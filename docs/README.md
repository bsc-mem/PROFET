# Documentation for PROFET

This directory contains the documentation for PROFET. The documentation is generated using Sphinx and is based on the docstrings found within the source code.

## For Users

To view the documentation, open <a href="docs/html/index.html" target="_blank">docs/html/index.html</a> file in your web browser.

## For Developers

If you've made changes to the docstrings in the source code or want to update the documentation, follow these steps:

1. Ensure you have all the required packages installed, especially Sphinx. If you haven't, you can install them with (from the `docs/` folder):
   ```bash
   pip install -r requirements.txt
   ```

2. From this `docs/` directory, run:
   ```bash
   make html
   ```

3. This command will generate (or regenerate) the HTML documentation in the `html` directory.
   
4. Review your changes by opening <a href="docs/html/index.html" target="_blank">docs/html/index.html</a> file in your web browser.

5. If everything looks good, commit your changes, including any modifications in the `html` directory, so that the updated documentation is available for all users.


### Troubleshooting Sphinx Documentation

If you encounter issues related to Sphinx documentation generation, you can try clearing the Sphinx cache to resolve them. Execute the following commands to remove cached files:

```bash
rm -r doctrees/ 
rm -r html/
```

After clearing the cache, regenerate the documentation with:

```bash
make html
```

### Updating the Documentation

When adding new functions or files that need to be included in the documentation, ensure to update the corresponding `.rst` file (in `source/` folder) accordingly. This ensures that all relevant content is appropriately documented and accessible to users.