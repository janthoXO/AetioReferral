// Data-only template: all visible text comes from the JSON in sys.inputs.data.
#let d = json(bytes(sys.inputs.data))
#let s = d.sender
#let r = d.recipient
#let ink = rgb("#222222")
#let grey = rgb("#666666")
#let red = rgb("#9b1c1c")
#let blue = rgb("#1f3a93")

#set text(font: "Carlito", size: 11pt, fill: ink, lang: d.lang)
#set par(leading: 0.62em, spacing: 1em, justify: false)
#set page(
  paper: "a4",
  margin: (left: 25mm, right: 20mm, top: 20mm, bottom: 22mm),
  footer: context {
    let n = counter(page).final().first()
    if n > 1 { align(right, text(9pt, fill: grey)[#counter(page).display() / #n]) }
  },
  background: {
    // fold and hole marks
    for (y, w) in ((105mm, 5mm), (210mm, 5mm), (148.5mm, 8mm)) {
      place(top + left, dy: y, line(length: w, stroke: 0.4pt + grey))
    }
    context if here().page() == 1 {
      // letterhead
      place(top + left, dx: 25mm, dy: 12mm, block(width: 165mm, {
        grid(columns: (1fr, auto), column-gutter: 8mm,
          {
            if s.practice != "" { text(19pt, weight: "bold", fill: blue.darken(30%), s.practice) }
            if s.name != "" { linebreak(); text(11.5pt, s.name) }
            if s.specialty != "" { linebreak(); text(10.5pt, fill: grey, s.specialty) }
          },
          align(right, text(9pt, fill: grey, {
            let rows = s.address + s.contact
            rows.join(linebreak())
            if s.identifiers.len() > 0 {
              if rows.len() > 0 { v(0.5em, weak: true) }
              text(8pt, s.identifiers.join(linebreak()))
            }
          })),
        )
        v(2.5mm)
        line(length: 100%, stroke: 0.5pt + blue.lighten(40%))
      }))
      // address field
      place(top + left, dx: 20mm, dy: 45mm, block(width: 85mm, height: 45mm, {
        let ret = ((s.practice,) + s.address).filter(x => x != "")
        if ret.len() > 0 {
          text(7pt, fill: grey, underline(ret.join(" · ")))
          v(3mm)
        }
        let lines = (r.practice, r.name, if r.specialty != r.practice { r.specialty } else { "" })
        let lines = lines.filter(x => x != "") + r.address
        text(11pt, lines.join(linebreak()))
      }))
      // date
      if d.date != "" {
        place(top + left, dx: 125mm, dy: 45mm, text(11pt, d.date))
      }
    }
  },
)

// "\n\n" = new paragraph, "\n" = line break; plain strings only, never evaluated.
#let prose(t) = if t != "" {
  t.split("\n\n").map(p => p.split("\n").join(linebreak())).join(parbreak())
}

#v(78mm)

#if d.referral != "" or d.urgent != none {
  grid(columns: (1fr, auto), column-gutter: 6mm, align: horizon,
    text(13pt, weight: "bold", d.referral),
    if d.urgent != none and d.urgent != "" {
      box(stroke: 1.2pt + red, inset: (x: 5pt, y: 3pt), radius: 1pt,
        text(10.5pt, weight: "bold", fill: red, upper(d.urgent)))
    },
  )
  v(1em)
}

#if d.patient != none {
  if d.patient.line != "" { text(weight: "bold", d.patient.line) }
  if d.patient.details != "" { linebreak(); text(9pt, fill: grey, d.patient.details) }
  v(1.2em)
}

#if d.salutation != "" { d.salutation; parbreak() }
#if d.intro != "" { prose(d.intro); v(0.4em) }

#for sec in d.sections {
  block(breakable: false, above: 0.9em, below: 0em, {
    if sec.heading != "" { text(weight: "bold", sec.heading); linebreak() }
    prose(sec.text)
  })
}

// Closing travels with the signature block, so it is never left alone at a page end.
#block(breakable: false, above: 1.2em, {
  if d.closing != "" { d.closing }
  v(0.5em)
  grid(columns: (60mm, 1fr), column-gutter: 4mm, align: top,
    {
      if s.signature != "" {
        v(4mm)
        rotate(-3deg, origin: left + bottom,
          text(font: "Herr Von Muellerhoff", size: 26pt, fill: blue.darken(55%), s.signature))
      }
      v(1mm)
      if s.name != "" { s.name }
      if s.specialty != "" { linebreak(); text(10pt, fill: grey, s.specialty) }
    },
    {
      let l = ((s.practice,) + s.address + s.identifiers).filter(x => x != "")
      if l.len() > 0 {
        pad(left: 6mm, top: 1mm, rotate(-4deg, origin: left + horizon,
          box(stroke: 1.3pt + blue.transparentize(25%), inset: (x: 7pt, y: 5pt), radius: 2pt,
            text(8pt, weight: "bold", fill: blue.transparentize(20%), align(center, l.join(linebreak())))
          )))
      }
    },
  )
})

#if d.attachments != none {
  block(breakable: false, above: 1.4em, {
    if d.attachments.heading != "" { text(weight: "bold", d.attachments.heading); linebreak() }
    for it in d.attachments.items { [– #it]; linebreak() }
  })
}
