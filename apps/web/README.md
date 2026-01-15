# JobPilot AI Frontend

A modern, production-ready Next.js frontend for the JobPilot AI platform. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## 🚀 Features

- **Modern Stack**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **UI Components**: shadcn/ui with Radix UI primitives
- **State Management**: TanStack React Query + Zustand
- **Authentication**: JWT with automatic token refresh
- **Forms**: react-hook-form with Zod validation
- **Animations**: Framer Motion for smooth interactions
- **Theming**: Dark/light mode with next-themes
- **Responsive**: Mobile-first design
- **Accessibility**: WCAG compliant components

## 📁 Project Structure

```
apps/web/
├── app/                          # Next.js App Router
│   ├── (public)/                # Public routes (no auth)
│   │   ├── page.tsx             # Landing page
│   │   ├── login/page.tsx       # Login page
│   │   └── register/page.tsx    # Register page
│   ├── app/                     # Protected routes
│   │   ├── layout.tsx           # App layout with sidebar
│   │   ├── dashboard/page.tsx   # Dashboard
│   │   ├── resumes/             # Resume management
│   │   ├── jobs/                # Job search
│   │   ├── matches/             # Job matches
│   │   ├── ai/                  # AI features
│   │   ├── tracker/             # Application tracker
│   │   ├── preferences/         # User preferences
│   │   └── settings/            # Settings
│   └── layout.tsx               # Root layout
├── components/                   # Reusable components
│   ├── ui/                      # shadcn/ui components
│   ├── layout/                  # Layout components
│   ├── resumes/                 # Resume-specific components
│   ├── jobs/                    # Job-specific components
│   └── common/                  # Common components
├── lib/                         # Utilities and API
│   ├── api/                     # API client and endpoints
│   └── utils/                   # Utility functions
├── hooks/                       # Custom React hooks
├── store/                       # Zustand stores
└── styles/                      # Global styles
```

## 🛠️ Setup Instructions

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running JobPilot AI backend (see `../api/README.md`)

### 1. Install Dependencies

```bash
cd apps/web
npm install
```

### 2. Environment Configuration

Copy the environment template:

```bash
cp .env.example .env.local
```

Update `.env.local` with your configuration:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# App Configuration  
NEXT_PUBLIC_APP_NAME="JobPilot AI"
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Environment
NODE_ENV=development
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000

### 4. Build for Production

```bash
npm run build
npm start
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking
- `npm run test` - Run tests (when configured)

## 🎨 UI Components

This project uses [shadcn/ui](https://ui.shadcn.com/) components built on top of Radix UI. All components are:

- **Accessible**: WCAG compliant with proper ARIA attributes
- **Customizable**: Built with Tailwind CSS and CSS variables
- **Consistent**: Following a unified design system
- **Type-safe**: Full TypeScript support

### Adding New Components

To add a new shadcn/ui component:

```bash
npx shadcn-ui@latest add [component-name]
```

## 🔐 Authentication Flow

The app implements a secure JWT authentication flow:

1. **Login/Register**: User credentials are sent to the backend
2. **Token Storage**: Access token stored in memory, refresh token in localStorage
3. **Auto Refresh**: Axios interceptor automatically refreshes expired tokens
4. **Route Protection**: Middleware protects `/app/*` routes
5. **Logout**: Clears tokens and redirects to login

### Protected Routes

All routes under `/app/*` require authentication. The middleware automatically:

- Redirects unauthenticated users to `/login`
- Preserves the intended destination for post-login redirect
- Redirects authenticated users away from public auth pages

## 📡 API Integration

The frontend communicates with the FastAPI backend through a robust API client:

### Features

- **Automatic Token Management**: Handles JWT refresh automatically
- **Error Handling**: Normalizes API errors with user-friendly messages
- **Rate Limit Handling**: Implements retry logic for 429 responses
- **Type Safety**: Full TypeScript interfaces for all API responses
- **Flexible Response Parsing**: Handles different backend response formats

### API Services

- `authApi` - Authentication (login, register, refresh)
- `resumeApi` - Resume management and ATS scoring
- `jobsApi` - Job search and discovery
- `matchesApi` - Job matching and recommendations
- `preferencesApi` - User preferences management
- `aiApi` - AI-powered features (optimization, interview prep)
- `trackerApi` - Application tracking

## 🎯 Key Features

### Dashboard
- Overview of resumes, ATS scores, and job matches
- Quick actions for common tasks
- Recent activity feed

### Resume Management
- Drag & drop file upload with progress
- ATS score calculation and breakdown
- Public scorecard sharing (privacy-safe)
- Multiple resume support

### Job Discovery
- Advanced search with filters
- Real-time job matching
- Explainable match scores
- Job detail views with application assistance

### AI Features
- Resume optimization for specific jobs
- Interview preparation with STAR method
- Skills gap analysis
- Career recommendations

### Application Tracking
- Kanban-style application pipeline
- Status updates and notes
- Interview scheduling
- Follow-up reminders

## 🎨 Design System

### Colors
- **Primary**: Blue (#3B82F6) - Main brand color
- **Secondary**: Gray (#6B7280) - Supporting elements
- **Success**: Green (#10B981) - Positive actions
- **Warning**: Yellow (#F59E0B) - Cautions
- **Destructive**: Red (#EF4444) - Errors and deletions

### Typography
- **Font**: Inter (system fallback)
- **Headings**: Bold weights (600-700)
- **Body**: Regular weight (400)
- **Captions**: Light weight (300)

### Spacing
- **Base unit**: 4px (0.25rem)
- **Common spacing**: 4px, 8px, 16px, 24px, 32px, 48px
- **Container padding**: 24px mobile, 32px desktop

## 📱 Responsive Design

The app is built mobile-first with breakpoints:

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

### Mobile Features
- Collapsible sidebar drawer
- Touch-friendly interactions
- Optimized form layouts
- Swipe gestures (where appropriate)

## ♿ Accessibility

The app follows WCAG 2.1 AA guidelines:

- **Keyboard Navigation**: All interactive elements accessible via keyboard
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: Minimum 4.5:1 ratio for text
- **Focus Management**: Visible focus indicators
- **Alternative Text**: Images have descriptive alt text

## 🚀 Performance

### Optimization Strategies
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: Webpack bundle analyzer
- **Lazy Loading**: Components and routes loaded on demand
- **Caching**: React Query for server state caching

### Performance Targets
- **Lighthouse Score**: 90+ across all metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1

## 🧪 Testing

### Testing Strategy
- **Unit Tests**: Component logic and utilities
- **Integration Tests**: API integration and user flows
- **E2E Tests**: Critical user journeys
- **Accessibility Tests**: Automated a11y checking

### Running Tests
```bash
npm run test          # Run unit tests
npm run test:e2e      # Run E2E tests (when configured)
npm run test:a11y     # Run accessibility tests (when configured)
```

## 🔧 Development Guidelines

### Code Style
- **ESLint**: Enforced code style and best practices
- **Prettier**: Consistent code formatting
- **TypeScript**: Strict type checking enabled
- **Conventional Commits**: Standardized commit messages

### Component Guidelines
- Use functional components with hooks
- Implement proper TypeScript interfaces
- Follow single responsibility principle
- Include JSDoc comments for complex logic
- Use proper error boundaries

### State Management
- **Server State**: TanStack React Query for API data
- **UI State**: Zustand for local UI state (modals, sidebar, etc.)
- **Form State**: react-hook-form for form management
- **URL State**: Next.js router for navigation state

## 🚀 Deployment

### Build Process
```bash
npm run build         # Create production build
npm run start         # Start production server
```

### Environment Variables
Ensure all required environment variables are set:

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_APP_URL` - Frontend app URL
- `NODE_ENV` - Environment (development/production)

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow code style**: Run `npm run lint` and `npm run type-check`
4. **Write tests**: Add tests for new functionality
5. **Commit changes**: Use conventional commit format
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

**Type Errors**
```bash
# Run type checking
npm run type-check
```

**API Connection Issues**
- Verify `NEXT_PUBLIC_API_BASE_URL` is correct
- Ensure backend is running on specified port
- Check CORS configuration in backend

**Authentication Issues**
- Clear localStorage: `localStorage.clear()`
- Check JWT token expiration
- Verify backend auth endpoints are working

### Getting Help

- **Documentation**: Check the `/docs` folder
- **Issues**: Create a GitHub issue with reproduction steps
- **Discussions**: Use GitHub Discussions for questions

---

**Built with ❤️ by the JobPilot AI Team**