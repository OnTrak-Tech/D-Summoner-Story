import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from '../components/StatCard';

describe('StatCard', () => {
    it('renders the title and value', () => {
        render(<StatCard title="Wins" value="42" />);

        expect(screen.getByText('Wins')).toBeInTheDocument();
        expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
        render(<StatCard title="KDA" value="3.5" subtitle="Great performance!" />);

        expect(screen.getByText('Great performance!')).toBeInTheDocument();
    });
});
