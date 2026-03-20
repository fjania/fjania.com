import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const bits = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/bits' }),
  schema: z.object({
    model: z.string(),
    name: z.string(),
    types: z.array(z.string()),
    brand: z.enum(['wp', 'ws', 'cmt']),
    shank: z.string(),
    max_rpm: z.number().nullable(),
    image: z.string(),
    url: z.string().url(),
    qty: z.number().default(1),
    status: z.enum(['in-stock', 'backorder', 'shipped', 'ordered']),
    status_date: z.string().nullable(),
    specs: z.array(z.object({
      label: z.string(),
      value: z.string(),
    })),
  }),
});

const species = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/species' }),
  schema: z.object({
    name: z.string(),
    scientific: z.string(),
    origin: z.string(),
    appearance: z.object({
      heartwood: z.string(),
      sapwood: z.string(),
      grain: z.string(),
      texture: z.string(),
      luster: z.string(),
    }),
    properties: z.object({
      janka: z.number(),
      density: z.string(),
      workability: z.string(),
      turning: z.string(),
      gluing: z.string(),
      finishing: z.string(),
    }),
    uses: z.array(z.string()),
    advantages: z.array(z.string()),
    challenges: z.array(z.string()),
    finishing_tips: z.array(z.string()),
    buying_tips: z.array(z.string()),
    fun_fact: z.string(),
    comparisons: z.array(z.object({
      title: z.string(),
      rows: z.array(z.record(z.string())),
    })),
    faqs: z.array(z.object({
      q: z.string(),
      a: z.string(),
    })),
  }),
});

const manuals = defineCollection({
  loader: glob({ pattern: '**/*.yml', base: './src/content/manuals' }),
  schema: z.object({
    name: z.string(),
    manufacturer: z.string(),
    model: z.string(),
    category: z.string(),
    pdf: z.string(),
    pages: z.number(),
    image: z.string(),
  }),
});

export const collections = { bits, species, manuals };
