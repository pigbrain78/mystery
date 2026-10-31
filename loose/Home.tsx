/*
Design philosophy for this page: Gallery House Eclecticism.
Use asymmetrical compositions, curatorial storytelling, warm editorial copy, arched motifs, and tactile spacing.
Avoid generic startup sections; every block should feel like a room in a collected house of ideas.
*/
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Compass,
  Frame,
  Globe2,
  Layers3,
  MoveUpRight,
  Sparkles,
} from "lucide-react";

const salons = [
  {
    id: "01",
    title: "Identity with atmosphere",
    text: "Pera shapes places, stories, and digital presence with the sensibility of a curator rather than the voice of a catalogue.",
    icon: Frame,
  },
  {
    id: "02",
    title: "Diversity with intention",
    text: "Every experience is composed from multiple visual languages, materials, and references so the result feels collected, not copied.",
    icon: Globe2,
  },
  {
    id: "03",
    title: "Craft with momentum",
    text: "The brand moves between strategy and atmosphere, building things that are as useful in motion as they are memorable on first contact.",
    icon: Layers3,
  },
];

const rooms = [
  {
    title: "Brand rooms",
    subtitle: "Identity systems, voice, and visual framing for ideas that need presence.",
  },
  {
    title: "Spatial moments",
    subtitle: "Environments, activations, and visual narratives that translate feeling into place.",
  },
  {
    title: "Digital salons",
    subtitle: "Web experiences that balance depth, clarity, and a sense of discovery.",
  },
];

const notes = [
  "Collected aesthetics rather than one-note branding.",
  "Editorial layouts with tactile materials and generous contrast.",
  "A voice that feels global, warm, and precise at the same time.",
];

const metrics = [
  { value: "07", label: "visual languages woven into one coherent identity" },
  { value: "24", label: "curated touchpoints imagined across physical and digital space" },
  { value: "∞", label: "ways a brand can feel human when craft guides the system" },
];

export default function Home() {
  return (
    <div className="pera-shell min-h-screen overflow-x-hidden bg-background text-foreground">
      <main className="relative">
        <section className="hero-room px-4 pb-10 pt-4 sm:px-6 lg:px-8 lg:pb-16 lg:pt-6">
          <div className="mx-auto grid max-w-[1500px] gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-stretch">
            <div className="hero-stage relative overflow-hidden rounded-[2rem] border border-white/40 bg-[#f4eee7] shadow-[0_30px_80px_rgba(25,28,39,0.16)]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.95),transparent_32%),linear-gradient(135deg,rgba(255,255,255,0.18),transparent_55%)]" />
              <img
                src="https://d2xsxph8kpxj0f.cloudfront.net/310519663536834203/KjifLmoPjV5BB5oi5XSE9g/pera-hero-arch-courtyard-dVzT3brj4cgfkRoCkDvMG5.webp"
                alt="Curated courtyard interior representing the Pera aesthetic"
                className="absolute inset-0 h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#f4eee7]/95 via-[#f4eee7]/72 to-[#0f1830]/12" />
              <div className="relative z-10 flex min-h-[720px] flex-col justify-between p-6 sm:p-8 lg:p-12">
                <div className="flex items-center justify-between gap-4">
                  <div className="inline-flex items-center gap-3 rounded-full border border-[#17324d]/15 bg-white/75 px-4 py-2 text-[0.72rem] uppercase tracking-[0.28em] text-[#17324d] backdrop-blur-sm">
                    <span className="h-2 w-2 rounded-full bg-[#b46a4e]" />
                    Pera
                  </div>
                  <div className="hidden rounded-full border border-[#17324d]/10 bg-white/70 px-4 py-2 text-[0.72rem] uppercase tracking-[0.28em] text-[#17324d] backdrop-blur-sm sm:block">
                    Unique and diverse by design
                  </div>
                </div>

                <div className="max-w-3xl space-y-8">
                  <div className="space-y-5">
                    <p className="max-w-sm text-[0.82rem] uppercase tracking-[0.34em] text-[#7c604f]">
                      A gallery house for culture, identity, and digital atmosphere
                    </p>
                    <h1 className="font-display text-6xl leading-[0.92] text-[#12253c] sm:text-7xl lg:text-[7.8rem]">
                      Pera
                    </h1>
                    <p className="max-w-2xl text-lg leading-8 text-[#304052] sm:text-xl">
                      Pera is imagined as a living collection of spaces, stories, and interfaces.
                      It brings together editorial elegance, multicultural texture, and modern
                      clarity to create a brand world that feels both intimate and expansive.
                    </p>
                  </div>

                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                    <Button className="group h-12 rounded-full bg-[#17324d] px-7 text-sm uppercase tracking-[0.2em] text-white hover:bg-[#0f2439]">
                      Enter the house
                      <ArrowRight className="ml-2 size-4 transition-transform duration-300 group-hover:translate-x-1" />
                    </Button>
                    <Button
                      variant="outline"
                      className="h-12 rounded-full border-[#17324d]/20 bg-white/72 px-7 text-sm uppercase tracking-[0.2em] text-[#17324d] backdrop-blur-sm hover:bg-white"
                    >
                      View the collection
                    </Button>
                  </div>
                </div>

                <div className="grid gap-4 border-t border-[#17324d]/10 pt-6 sm:grid-cols-3">
                  {metrics.map((metric) => (
                    <div key={metric.label} className="rounded-[1.5rem] bg-white/66 p-4 backdrop-blur-sm">
                      <div className="font-display text-4xl text-[#12253c]">{metric.value}</div>
                      <p className="mt-2 max-w-[18rem] text-sm leading-6 text-[#425062]">
                        {metric.label}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <aside className="grid gap-6 lg:grid-rows-[1.05fr_0.95fr]">
              <div className="relative overflow-hidden rounded-[2rem] border border-[#17324d]/10 bg-[#12253c] text-white shadow-[0_24px_60px_rgba(18,37,60,0.18)]">
                <img
                  src="https://d2xsxph8kpxj0f.cloudfront.net/310519663536834203/KjifLmoPjV5BB5oi5XSE9g/pera-night-salon-window-mDaVvMNZNauf3PLN3vJi7v.webp"
                  alt="Atmospheric salon corner at dusk"
                  className="absolute inset-0 h-full w-full object-cover opacity-55"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-[#10253d]/35 via-[#10253d]/55 to-[#10253d]/92" />
                <div className="relative z-10 flex h-full flex-col justify-between p-7">
                  <div className="flex items-center justify-between text-sm uppercase tracking-[0.24em] text-white/70">
                    <span>Curator note</span>
                    <Sparkles className="size-4" />
                  </div>
                  <div className="space-y-4">
                    <h2 className="font-display text-4xl leading-tight text-white">
                      A brand should feel like a place people remember.
                    </h2>
                    <p className="max-w-md text-base leading-7 text-white/80">
                      Pera is not framed as a single service. It is a house of distinct moods,
                      perspectives, and crafted experiences, connected by taste and narrative.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative overflow-hidden rounded-[2rem] border border-[#17324d]/10 bg-[#efe7dd] p-6 shadow-[0_20px_50px_rgba(47,36,29,0.1)]">
                <img
                  src="https://d2xsxph8kpxj0f.cloudfront.net/310519663536834203/KjifLmoPjV5BB5oi5XSE9g/pera-paper-texture-panel-B4LP7YgaFnNr9qnfAf8Sha.webp"
                  alt="Layered paper and copper art texture"
                  className="absolute -right-8 -top-10 h-[70%] w-auto opacity-80"
                />
                <div className="relative z-10 space-y-5">
                  <div className="flex items-center justify-between">
                    <span className="text-[0.72rem] uppercase tracking-[0.28em] text-[#7b5a48]">
                      Composition
                    </span>
                    <Compass className="size-4 text-[#17324d]" />
                  </div>
                  <div className="space-y-3 pr-16">
                    <h3 className="font-display text-3xl leading-tight text-[#12253c]">
                      Warm structure, collected detail, contemporary rhythm.
                    </h3>
                    <p className="text-sm leading-7 text-[#475566]">
                      The visual language blends archways, textured surfaces, dark-blue depth,
                      and soft apricot light to make the site feel curated rather than templated.
                    </p>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section className="salon-grid px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
          <div className="mx-auto grid max-w-[1500px] gap-6 lg:grid-cols-[0.72fr_1.28fr]">
            <div className="rounded-[2rem] border border-[#17324d]/10 bg-white/80 p-8 shadow-[0_16px_45px_rgba(20,24,38,0.08)] backdrop-blur-sm">
              <p className="text-[0.72rem] uppercase tracking-[0.28em] text-[#7b5a48]">House principles</p>
              <h2 className="mt-5 font-display text-4xl leading-tight text-[#12253c]">
                Distinct rooms for a broader identity.
              </h2>
              <div className="mt-8 space-y-4">
                {notes.map((note) => (
                  <div
                    key={note}
                    className="rounded-[1.35rem] border border-[#17324d]/10 bg-[#f6f0ea] px-5 py-4 text-sm leading-7 text-[#304052]"
                  >
                    {note}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              {salons.map((item) => {
                const Icon = item.icon;
                return (
                  <article
                    key={item.id}
                    className="group relative overflow-hidden rounded-[2rem] border border-[#17324d]/10 bg-white/80 p-7 shadow-[0_18px_45px_rgba(20,24,38,0.08)] transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_26px_60px_rgba(20,24,38,0.14)]"
                  >
                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#17324d] via-[#b06c58] to-[#dfba8a] opacity-80" />
                    <div className="flex items-center justify-between">
                      <span className="font-label text-sm tracking-[0.2em] text-[#8d6d5b]">{item.id}</span>
                      <Icon className="size-5 text-[#17324d]" />
                    </div>
                    <h3 className="mt-12 font-display text-3xl leading-tight text-[#12253c]">
                      {item.title}
                    </h3>
                    <p className="mt-5 text-sm leading-7 text-[#4e5d6d]">{item.text}</p>
                    <div className="mt-8 inline-flex items-center gap-2 text-sm uppercase tracking-[0.2em] text-[#17324d]">
                      Learn the language
                      <MoveUpRight className="size-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section className="showcase-room px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
          <div className="mx-auto grid max-w-[1500px] gap-6 lg:grid-cols-[1.12fr_0.88fr]">
            <div className="relative overflow-hidden rounded-[2.2rem] border border-[#17324d]/10 bg-[#f3ede5] shadow-[0_20px_55px_rgba(18,37,60,0.1)]">
              <img
                src="https://d2xsxph8kpxj0f.cloudfront.net/310519663536834203/KjifLmoPjV5BB5oi5XSE9g/pera-collection-still-life-NR7KYYpfLeaXaTFz3pQ3Li.webp"
                alt="Still life collection showing layered objects and references"
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#f3ede5]/90 via-[#f3ede5]/25 to-transparent" />
              <div className="absolute left-6 top-6 max-w-xs rounded-[1.4rem] border border-white/50 bg-white/70 p-5 backdrop-blur-md sm:left-8 sm:top-8">
                <p className="text-[0.72rem] uppercase tracking-[0.28em] text-[#7b5a48]">Collected references</p>
                <p className="mt-3 text-sm leading-7 text-[#304052]">
                  Pera draws from interiors, archives, language, movement, and hospitality to make each digital surface feel inhabited.
                </p>
              </div>
            </div>

            <div className="grid gap-6">
              <div className="rounded-[2rem] border border-[#17324d]/10 bg-[#12253c] p-8 text-white shadow-[0_20px_55px_rgba(18,37,60,0.16)]">
                <p className="text-[0.72rem] uppercase tracking-[0.28em] text-white/60">What Pera can hold</p>
                <div className="mt-6 space-y-5">
                  {rooms.map((room) => (
                    <div key={room.title} className="border-b border-white/12 pb-5 last:border-b-0 last:pb-0">
                      <h3 className="font-display text-3xl text-white">{room.title}</h3>
                      <p className="mt-2 text-sm leading-7 text-white/74">{room.subtitle}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[2rem] border border-[#17324d]/10 bg-white/80 p-8 shadow-[0_18px_45px_rgba(20,24,38,0.08)]">
                <p className="text-[0.72rem] uppercase tracking-[0.28em] text-[#7b5a48]">Editorial premise</p>
                <h3 className="mt-4 font-display text-4xl leading-tight text-[#12253c]">
                  More house than homepage. More atmosphere than brochure.
                </h3>
                <p className="mt-5 text-base leading-8 text-[#475566]">
                  This concept site imagines Pera as a refined, expansive identity that can hold
                  strategy, design, culture, and experience under one roof without flattening any of them.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="manifest-room px-4 pb-16 pt-8 sm:px-6 lg:px-8 lg:pb-24 lg:pt-14">
          <div className="mx-auto grid max-w-[1500px] gap-6 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="rounded-[2rem] border border-[#17324d]/10 bg-[#efe6db] p-8 shadow-[0_18px_45px_rgba(20,24,38,0.08)]">
              <p className="text-[0.72rem] uppercase tracking-[0.28em] text-[#7b5a48]">From the threshold</p>
              <h2 className="mt-5 font-display text-5xl leading-[0.96] text-[#12253c]">
                A unique and diverse brand world should still feel coherent.
              </h2>
            </div>

            <div className="rounded-[2rem] border border-[#17324d]/10 bg-white/80 p-8 shadow-[0_18px_45px_rgba(20,24,38,0.08)]">
              <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
                <div>
                  <p className="text-lg leading-8 text-[#304052]">
                    Pera is presented here as a house of gathered perspectives. The architecture is
                    modern, the tone is warm, and the visual language is intentionally layered. It
                    invites visitors into a brand identity that feels lived in, thoughtful, and quietly memorable.
                  </p>
                  <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                    <Button className="group h-12 rounded-full bg-[#b06c58] px-7 text-sm uppercase tracking-[0.2em] text-white hover:bg-[#9d5b49]">
                      Start a new chapter
                      <ArrowRight className="ml-2 size-4 transition-transform duration-300 group-hover:translate-x-1" />
                    </Button>
                    <Button
                      variant="outline"
                      className="h-12 rounded-full border-[#17324d]/20 bg-transparent px-7 text-sm uppercase tracking-[0.2em] text-[#17324d] hover:bg-[#f6f0ea]"
                    >
                      Read the curator note
                    </Button>
                  </div>
                </div>

                <div className="rounded-[1.6rem] bg-[#12253c] p-6 text-white">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[0.72rem] uppercase tracking-[0.28em] text-white/55">Pera promise</p>
                      <p className="mt-3 font-display text-3xl leading-tight">A world with range, held together by taste.</p>
                    </div>
                    <div className="rounded-full border border-white/15 p-3">
                      <Globe2 className="size-5" />
                    </div>
                  </div>
                  <p className="mt-5 text-sm leading-7 text-white/72">
                    Built to feel distinctive on first view and coherent over time, this direction turns a name into a place visitors can return to.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
