# Architecture First Pass

This repo now has the first layer of the larger system: page recognition.

The intended stack is:

```txt
source Markdown or HTML
-> label_structure.py
-> component manifest
-> human GUI or AI edits component controls
-> compiler rebuilds HTML
-> validator catches broken output
```

The first pass does not try to solve all layout decisions. It labels the work surface.

Current recognized component types:
- `heading`
- `paragraph`
- `image`
- `semantic_block`
- `quote`
- `html_component` for topbar/nav/hero/sidebar/footer-like HTML

The important object is the component manifest:

```txt
component_manifests/*.components.yml
```

Each component gets:
- stable `id`
- component `type`
- semantic `role`
- source location
- editable `controls`
- optional locks

The next build step should consume this manifest. For example, if `image_001.controls.align` changes from `center` to `right`, the compiler should render the image with the matching class or wrapper.

Do not make this a single mega-script. Keep the layers separate:

```txt
detect -> represent -> edit -> rebuild -> validate
```
