# KaiCalls Component Examples

Real-world component patterns from the KaiCalls codebase.

## Table of Contents
1. [Dashboard Page Layout](#dashboard-page-layout)
2. [Data Table with Actions](#data-table-with-actions)
3. [Form with Validation](#form-with-validation)
4. [Settings Panel](#settings-panel)
5. [Empty State](#empty-state)
6. [Loading Skeletons](#loading-skeletons)
7. [Alert Patterns](#alert-patterns)
8. [Dropdown Menu](#dropdown-menu)
9. [Tabs Pattern](#tabs-pattern)
10. [Stat Dashboard](#stat-dashboard)

## Dashboard Page Layout

Complete dashboard page with header, stats, and content:

```tsx
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Phone, Users, TrendingUp, Calendar } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="heading-xl">Dashboard</h1>
          <p className="text-body-secondary mt-1">
            Overview of your AI assistant performance
          </p>
        </div>
        <Button>
          <Phone className="mr-2 h-4 w-4" />
          Test Call
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Calls"
          value="1,234"
          change="+12%"
          changeType="positive"
          icon={Phone}
        />
        <StatCard
          label="Leads Captured"
          value="456"
          change="+8%"
          changeType="positive"
          icon={Users}
        />
        <StatCard
          label="Conversion Rate"
          value="37%"
          change="-2%"
          changeType="negative"
          icon={TrendingUp}
        />
        <StatCard
          label="Avg Call Duration"
          value="4:32"
          change="+15s"
          changeType="neutral"
          icon={Calendar}
        />
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Calls</CardTitle>
            <CardDescription>Your latest AI assistant interactions</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Table or list content */}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hot Leads</CardTitle>
            <CardDescription>Leads requiring immediate attention</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Lead list content */}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ label, value, change, changeType, icon: Icon }) {
  const changeColor = {
    positive: "text-kai-success-text",
    negative: "text-kai-error-text",
    neutral: "text-muted-foreground"
  }[changeType];

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <span className="stat-label">{label}</span>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="data-value">{value}</span>
          <span className={`text-sm ${changeColor}`}>{change}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Data Table with Actions

Table with sorting, selection, and row actions:

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, ArrowUpDown } from "lucide-react";

export function LeadsTable({ leads }) {
  return (
    <div className="rounded-md border border-kai-table-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox />
            </TableHead>
            <TableHead>
              <Button variant="ghost" size="sm" className="-ml-3">
                Name
                <ArrowUpDown className="ml-2 h-4 w-4" />
              </Button>
            </TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Temperature</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leads.map((lead) => (
            <TableRow key={lead.id} className="table-row">
              <TableCell>
                <Checkbox />
              </TableCell>
              <TableCell className="font-medium">{lead.name}</TableCell>
              <TableCell className="text-muted-foreground">{lead.phone}</TableCell>
              <TableCell>
                <TemperatureBadge temperature={lead.temperature} />
              </TableCell>
              <TableCell>
                <StatusBadge status={lead.status} />
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>View Details</DropdownMenuItem>
                    <DropdownMenuItem>Call Back</DropdownMenuItem>
                    <DropdownMenuItem>Send Email</DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                      Archive
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function TemperatureBadge({ temperature }) {
  const className = {
    hot: "badge-hot",
    warm: "badge-warm",
    cold: "badge-cold"
  }[temperature];

  return <span className={className}>{temperature}</span>;
}

function StatusBadge({ status }) {
  const className = {
    new: "status-info",
    contacted: "status-warning",
    qualified: "status-success",
    lost: "status-error"
  }[status];

  return <span className={className}>{status}</span>;
}
```

## Form with Validation

Form with error states and validation feedback:

```tsx
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle } from "lucide-react";

export function AgentForm({ onSubmit }) {
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Agent</CardTitle>
        <CardDescription>
          Set up a new AI assistant for your business
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Error Alert */}
        {errors.general && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{errors.general}</AlertDescription>
          </Alert>
        )}

        {/* Name Field */}
        <div className="space-y-2">
          <Label htmlFor="name">Agent Name</Label>
          <Input
            id="name"
            placeholder="e.g., Sales Assistant"
            className={errors.name ? "border-destructive" : ""}
          />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name}</p>
          )}
        </div>

        {/* Voice Field */}
        <div className="space-y-2">
          <Label htmlFor="voice">Voice</Label>
          <Select>
            <SelectTrigger className={errors.voice ? "border-destructive" : ""}>
              <SelectValue placeholder="Select a voice" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="sarah">Sarah (Female, Professional)</SelectItem>
              <SelectItem value="james">James (Male, Friendly)</SelectItem>
              <SelectItem value="emma">Emma (Female, Warm)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Greeting Field */}
        <div className="space-y-2">
          <Label htmlFor="greeting">Greeting Message</Label>
          <Textarea
            id="greeting"
            placeholder="Hi! Thanks for calling..."
            rows={3}
            className={errors.greeting ? "border-destructive" : ""}
          />
          <p className="text-xs text-muted-foreground">
            This is what your agent says when answering a call
          </p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create Agent
        </Button>
      </CardFooter>
    </Card>
  );
}
```

## Settings Panel

Settings page with sections and toggles:

```tsx
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export function SettingsPanel() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="heading-xl">Settings</h1>
        <p className="text-body-secondary mt-1">
          Manage your account and preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>
            Configure how you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <SettingRow
            label="Email Notifications"
            description="Receive email alerts for new leads"
            defaultChecked={true}
          />
          <Separator />
          <SettingRow
            label="SMS Notifications"
            description="Get text messages for hot leads"
            defaultChecked={false}
          />
          <Separator />
          <SettingRow
            label="Browser Notifications"
            description="Show desktop notifications"
            defaultChecked={true}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Privacy</CardTitle>
          <CardDescription>
            Control your privacy settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <SettingRow
            label="Call Recording"
            description="Record all incoming calls for quality assurance"
            defaultChecked={true}
          />
          <Separator />
          <SettingRow
            label="Analytics"
            description="Share anonymous usage data to improve the product"
            defaultChecked={false}
          />
        </CardContent>
      </Card>
    </div>
  );
}

function SettingRow({ label, description, defaultChecked }) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <Label className="text-base">{label}</Label>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch defaultChecked={defaultChecked} />
    </div>
  );
}
```

## Empty State

Engaging empty state with illustration and CTA:

```tsx
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Phone, Plus, Sparkles } from "lucide-react";

export function EmptyLeadsState() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16">
        {/* Illustration */}
        <div className="rounded-full bg-secondary p-4 mb-6">
          <Phone className="h-8 w-8 text-kai-blue" />
        </div>

        {/* Copy */}
        <h3 className="heading-md mb-2">No leads yet</h3>
        <p className="text-body-secondary text-center max-w-sm mb-6">
          When callers reach your AI assistant, their information will appear here
          automatically.
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Add Lead Manually
          </Button>
          <Button>
            <Sparkles className="mr-2 h-4 w-4" />
            Create Agent
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function EmptyCallsState() {
  return (
    <div className="text-center py-12">
      <div className="mx-auto w-24 h-24 rounded-full bg-gradient-kai opacity-20 mb-6" />
      <h3 className="heading-md mb-2">Ready for your first call</h3>
      <p className="text-body-secondary max-w-md mx-auto mb-6">
        Your AI assistant is standing by. Share your phone number with customers
        to start receiving calls.
      </p>
      <Button>View Phone Number</Button>
    </div>
  );
}
```

## Loading Skeletons

Skeleton loaders matching content structure:

```tsx
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-4 w-4 rounded" />
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <Skeleton className="h-8 w-16" />
          <Skeleton className="h-4 w-10" />
        </div>
      </CardContent>
    </Card>
  );
}

export function TableRowSkeleton() {
  return (
    <tr>
      <td className="px-4 py-3"><Skeleton className="h-4 w-4" /></td>
      <td className="px-4 py-3"><Skeleton className="h-4 w-32" /></td>
      <td className="px-4 py-3"><Skeleton className="h-4 w-24" /></td>
      <td className="px-4 py-3"><Skeleton className="h-5 w-12 rounded-full" /></td>
      <td className="px-4 py-3"><Skeleton className="h-5 w-16 rounded-full" /></td>
      <td className="px-4 py-3"><Skeleton className="h-8 w-8 rounded" /></td>
    </tr>
  );
}

export function LeadsTableSkeleton() {
  return (
    <div className="rounded-md border border-kai-table-border">
      <table className="w-full">
        <thead>
          <tr>
            <th className="px-4 py-3"><Skeleton className="h-4 w-4" /></th>
            <th className="px-4 py-3 text-left"><Skeleton className="h-4 w-16" /></th>
            <th className="px-4 py-3 text-left"><Skeleton className="h-4 w-12" /></th>
            <th className="px-4 py-3 text-left"><Skeleton className="h-4 w-20" /></th>
            <th className="px-4 py-3 text-left"><Skeleton className="h-4 w-14" /></th>
            <th className="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRowSkeleton key={i} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-48 mt-2" />
        </div>
        <Skeleton className="h-10 w-24" />
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>

      {/* Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-48 mt-1" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-4 w-40 mt-1" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

## Alert Patterns

Different alert types and usage:

```tsx
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from "lucide-react";

// Success Alert
export function SuccessAlert({ message, onDismiss }) {
  return (
    <Alert className="bg-kai-success-bg border-kai-success-text/20">
      <CheckCircle className="h-4 w-4 text-kai-success-text" />
      <AlertTitle className="text-kai-success-text">Success</AlertTitle>
      <AlertDescription className="text-kai-success-text/80">
        {message}
      </AlertDescription>
      {onDismiss && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-2 top-2"
          onClick={onDismiss}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </Alert>
  );
}

// Error Alert
export function ErrorAlert({ title, message }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title || "Something went wrong"}</AlertTitle>
      <AlertDescription>
        {message || "We're looking into it. Try refreshing the page."}
      </AlertDescription>
    </Alert>
  );
}

// Warning Alert
export function WarningAlert({ message }) {
  return (
    <Alert className="bg-kai-warning-bg border-kai-warning-text/20">
      <AlertTriangle className="h-4 w-4 text-kai-warning-text" />
      <AlertTitle className="text-kai-warning-text">Warning</AlertTitle>
      <AlertDescription className="text-kai-warning-text/80">
        {message}
      </AlertDescription>
    </Alert>
  );
}

// Info Alert
export function InfoAlert({ message }) {
  return (
    <Alert className="bg-kai-info-bg border-kai-info-text/20">
      <Info className="h-4 w-4 text-kai-info-text" />
      <AlertTitle className="text-kai-info-text">Note</AlertTitle>
      <AlertDescription className="text-kai-info-text/80">
        {message}
      </AlertDescription>
    </Alert>
  );
}
```

## Dropdown Menu

Dropdown with sections and icons:

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Settings, CreditCard, LogOut, HelpCircle } from "lucide-react";

export function UserMenu({ user }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-kai-blue text-white">
              {user.initials}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user.name}</p>
            <p className="text-xs text-muted-foreground">{user.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>
            <User className="mr-2 h-4 w-4" />
            Profile
            <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <Settings className="mr-2 h-4 w-4" />
            Settings
            <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem>
            <CreditCard className="mr-2 h-4 w-4" />
            Billing
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem>
          <HelpCircle className="mr-2 h-4 w-4" />
          Help & Support
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive">
          <LogOut className="mr-2 h-4 w-4" />
          Log out
          <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

## Tabs Pattern

Tabs for content organization:

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AgentDetailsTabs({ agent }) {
  return (
    <Tabs defaultValue="overview" className="space-y-6">
      <TabsList className="bg-secondary">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="calls">Calls</TabsTrigger>
        <TabsTrigger value="leads">Leads</TabsTrigger>
        <TabsTrigger value="settings">Settings</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Stat cards */}
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Performance Overview</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Charts */}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="calls">
        <Card>
          <CardHeader>
            <CardTitle>Call History</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Calls table */}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="leads">
        <Card>
          <CardHeader>
            <CardTitle>Captured Leads</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Leads table */}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="settings">
        {/* Settings form */}
      </TabsContent>
    </Tabs>
  );
}
```

## Stat Dashboard

Data visualization dashboard:

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkline } from "@/components/ui/sparkline";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function StatsDashboard({ stats }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <span className="stat-label">{stat.label}</span>
              <TrendIcon change={stat.changePercent} />
            </div>

            <div className="mt-2">
              <span className="data-value">{stat.value}</span>
              <ChangeIndicator
                value={stat.changePercent}
                label={stat.changeLabel}
              />
            </div>

            {/* Mini sparkline */}
            {stat.sparklineData && (
              <div className="mt-4 h-8">
                <Sparkline
                  data={stat.sparklineData}
                  color={stat.changePercent >= 0 ? "#34D399" : "#FF4B4B"}
                />
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TrendIcon({ change }) {
  if (change > 0) {
    return <TrendingUp className="h-4 w-4 text-kai-success-text" />;
  } else if (change < 0) {
    return <TrendingDown className="h-4 w-4 text-kai-error-text" />;
  }
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

function ChangeIndicator({ value, label }) {
  const isPositive = value > 0;
  const isNegative = value < 0;

  const colorClass = isPositive
    ? "text-kai-success-text"
    : isNegative
    ? "text-kai-error-text"
    : "text-muted-foreground";

  const prefix = isPositive ? "+" : "";

  return (
    <span className={`text-sm ${colorClass} ml-2`}>
      {prefix}{value}% {label}
    </span>
  );
}
```
