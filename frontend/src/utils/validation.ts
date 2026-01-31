import { z } from 'zod';

export const PlatformEnum = z.enum(['riot', 'steam', 'xbox', 'psn']);

export const RegionEnum = z.enum([
  'na1',
  'euw1',
  'eun1',
  'kr',
  'br1',
  'la1',
  'la2',
  'oc1',
  'ru',
  'tr1',
  'jp1',
  'sg2',
  'tw2',
  'vn2',
]);

export const PlayerInputSchema = z
  .object({
    platform: PlatformEnum,
    playerId: z
      .string()
      .min(3, 'Player ID must be at least 3 characters')
      .max(32, 'Player ID must be less than 32 characters')
      .trim(),
    region: RegionEnum.optional(),
  })
  .refine(
    (data) => {
      if (data.platform === 'riot' && !data.region) {
        return false;
      }
      return true;
    },
    {
      message: 'Region is required for Riot Games',
      path: ['region'],
    }
  );

export type PlayerInputData = z.infer<typeof PlayerInputSchema>;
